"""E7 laboratory: provenance-locked generic linkage CSV -> planar E1 solver spec.

Reads source-authored positions, rigid body membership, joint endpoints, slot
lines, and angular driver. NO mechanism-name branching. No LLM inference.
Only handles continuous, planar sources expressible by E1; rejects all others.
A successful import is NOT recognition of machines from text or CAD geometry.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import ssl
from pathlib import Path
from urllib.request import Request, build_opener, HTTPSHandler

from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos.ingestao_evidencias_f16 import NoRedirect

MANIFEST_SCHEMA="coringa-e7-upstream-geometry-manifest-v1"
HOST="https://raw.githubusercontent.com"
REPOSITORY="jackhale98/linkage_design"
COMMIT="c1ae13b040213b55ece567418bc14e4d2c8d1b0f"
IDENT=re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,35}$")
SHA=re.compile(r"^[a-f0-9]{40}$")
UNITS={"mm":.001,"cm":.01,"m":1.,"in":.0254}
MAX_BYTES=80000

def fail(reason):
    raise ValueError("E7-FONTE-"+reason)

def git_blob_sha1(payload):
    return hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\0"+payload).hexdigest()

def source_manifest(manifest):
    if not isinstance(manifest,dict) or manifest.get("schema")!=MANIFEST_SCHEMA:
        fail("MANIFESTO")
    if (manifest.get("upstream_repository")!=REPOSITORY
        or manifest.get("upstream_commit")!=COMMIT
        or manifest.get("upstream_license")!="MIT"
        or manifest.get("upstream_license_path")!="LICENSE"
        or not SHA.fullmatch(str(manifest.get("upstream_license_git_blob_sha1","")))
        or manifest.get("source_origin")!=HOST
        or manifest.get("publish") is not False):
        fail("FONTE_LICENCA")
    entries=manifest.get("files")
    if not isinstance(entries,list) or not 3<=len(entries)<=16:
        fail("MANIFESTO")
    if len({row["path"] for row in entries})!=len(entries):
        fail("MANIFESTO_DUPLICADO")
    for row in entries:
        if (set(row)!={"path","blob_sha1","group"}
            or type(row["path"]) is not str
            or not re.fullmatch(r"src/examples/[a-z][a-z0-9-]{0,55}\.csv",row["path"])
            or not SHA.fullmatch(str(row["blob_sha1"]))):
            fail("CAMINHO_OU_HASH")
    return entries

def fetch_pinned(path):
    if path!="LICENSE" and not re.fullmatch(
            r"src/examples/[a-z][a-z0-9-]{0,55}\.csv",path):
        fail("CAMINHO")
    url=f"{HOST}/{REPOSITORY}/{COMMIT}/{path}"
    req=Request(url,headers={
        "User-Agent":"Coringa-LAB-E7-Provenance/1.0 (+github.com/Heitor2404/coringa-news)",
        "Accept":"text/plain","Accept-Encoding":"identity"})
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req,timeout=12) as response:
            if response.status!=200 or response.url!=url:
                fail("REDIRECT")
            payload=response.read(MAX_BYTES+1)
    except ValueError:
        raise
    except (OSError,TimeoutError) as err:
        fail("DOWNLOAD_"+type(err).__name__)
    if not payload or len(payload)>MAX_BYTES:
        fail("TAMANHO")
    return payload

def sections(payload):
    if not isinstance(payload,bytes) or len(payload)>MAX_BYTES:fail("CSV_BYTES")
    try:text=payload.decode("utf-8-sig")
    except UnicodeDecodeError:fail("CSV_UTF8")
    if "\x00" in text:fail("CSV_NUL")
    reader=csv.reader(io.StringIO(text,newline=""),strict=True)
    result={};section=None;header=None
    try:
        for nr,raw in enumerate(reader,1):
            if not raw or all(not x.strip() for x in raw):continue
            row=[x.strip() for x in raw]
            if row[0].startswith("#"):continue
            if section is None:
                if row!=["LinkageDesign","1"]:fail("VERSAO")
                section="__header__";continue
            if len(row)==1 and re.fullmatch(r"\[[a-z_]+\]",row[0]):
                section=row[0][1:-1]
                if section in result:fail("SECAO_DUPLICADA")
                result[section]=[];header=None;continue
            if section=="__header__":fail("SECAO")
            if header is None:
                header=row
                if len(set(header))!=len(header) or "id" not in header and section not in (
                      "project","driver","motion","analysis"):
                    fail("CABECALHO")
                continue
            if len(row)!=len(header):fail("CSV_COLUNAS")
            result[section].append(dict(zip(header,row)))
            if len(result[section])>250:fail("LINHAS")
    except csv.Error:
        fail("CSV_MALFORMADO")
    if not {"project","points","lines","constraints","bodies","joints","driver"}<=set(result):
        fail("SECOES_REQUERIDAS")
    if set(result)-{"project","points","lines","constraints","bodies","joints",
                    "driver","motion","loads","analysis","pairs","cams","cam_segments"}:
        fail("SECAO_DESCONHECIDA")
    return result

def kv(rows):
    if not all(set(r)=={"key","value"} for r in rows):
        fail("CHAVE_VALOR")
    out={r["key"]:r["value"] for r in rows}
    if len(out)!=len(rows):fail("CHAVE_DUPLICADA")
    return out

def num(value):
    try:v=float(value)
    except (TypeError,ValueError):fail("NUMERO")
    if not math.isfinite(v) or abs(v)>100000:fail("NUMERO")
    return v

def distance(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])

def source_geometry(source):
    table=sections(source)
    project=kv(table["project"])
    unit=project.get("length_unit","")
    if unit not in UNITS or project.get("angle_unit")!="deg":fail("UNIDADE")
    factor=UNITS[unit]
    if table.get("pairs") or table.get("cams") or table.get("cam_segments"):
        fail("CONTATO_COMPOSTO_NAO_SUPORTADO")
    pts={}
    for p in table["points"]:
        name=p["id"]
        if not IDENT.fullmatch(name) or name in pts:fail("PONTO_DUPLICADO")
        pts[name]=(num(p["x"])*factor,num(p["y"])*factor)
    lines={}
    for line in table["lines"]:
        name=line["id"]
        if not IDENT.fullmatch(name) or name in lines:fail("LINHA_DUPLICADA")
        a=line["p1"];b=line["p2"]
        if a not in pts or b not in pts or a==b or distance(pts[a],pts[b])<1e-7:
            fail("LINHA_INCOERENTE")
        lines[name]=(a,b)
    if not 3<=len(pts)<=120 or not 2<=len(lines)<=100:fail("GEOMETRIA_TAMANHO")

    # Verify independent dimensions/alignments stored by the source CSV.
    # This prevents treating an internally inconsistent drawing as accurate.
    verified_constraints=0
    for c in table["constraints"]:
        kind=c["type"];a=c["a"];b=c["b"];value=c["value"]
        if c.get("reference") in ("1","true","yes"):
            fail("DIMENSAO_APENAS_REFERENCIA")
        measured=None;expected=0.
        if kind=="distance":
            if a in lines and not b:
                p1,p2=lines[a];measured=distance(pts[p1],pts[p2])
            elif a in pts and b in pts:
                measured=distance(pts[a],pts[b])
            else:fail("DISTANCIA_NAO_SUPORTADA")
            expected=num(value)*factor
            if expected<=0:fail("DISTANCIA_NEGATIVA")
        elif kind=="angle" and a in lines and not b:
            p1,p2=lines[a]
            d=(pts[p2][0]-pts[p1][0],pts[p2][1]-pts[p1][1])
            measured=math.degrees(math.atan2(d[1],d[0]))
            expected=num(value)
            measured=(measured-expected+180)%360-180
            expected=0.
        elif kind in ("horizontal","vertical") and a in lines and not b:
            p1,p2=lines[a]
            measured=(pts[p1][1]-pts[p2][1]) if kind=="horizontal" else (
                      pts[p1][0]-pts[p2][0])
        elif kind=="point_on_line" and a in pts and b in lines:
            p1,p2=lines[b];u=pts[p1];v=pts[p2];p=pts[a]
            measured=((p[0]-u[0])*(v[1]-u[1])-
                      (p[1]-u[1])*(v[0]-u[0]))/distance(u,v)
        elif kind=="midpoint" and a in pts and b in lines:
            p1,p2=lines[b];p=pts[a]
            measured=distance(p,((pts[p1][0]+pts[p2][0])/2,
                                 (pts[p1][1]+pts[p2][1])/2))
        else:
            fail("RESTRICAO_NAO_SUPORTADA")
        tolerance=1e-5 if kind=="angle" else 1e-6
        if abs(measured-expected)>tolerance:fail("DESENHO_NAO_SATISFAZ_CONSTRAINT")
        verified_constraints+=1

    owners={};bodies=[];body_lines={};origins={}
    if not 2<=len(table["bodies"])<=12:fail("QUANTIDADE_CORPOS")
    for b in table["bodies"]:
        original=b["id"];name=original.lower()
        if not IDENT.fullmatch(original) or not S.NAME.fullmatch(name):
            fail("CORPO_ID")
        if b.get("ground") not in ("","0","false"):fail("GROUND_MOVEL")
        if name in origins:fail("CORPO_DUPLICADO")
        members=b["lines"].split()
        if not members:fail("CORPO_SEM_LINHAS")
        if any(line not in lines or line in owners or
               table["lines"][[r["id"] for r in table["lines"]].index(line)].get("construction")=="1"
               for line in members):
            fail("LINHA_CORPO")
        for line in members:owners[line]=name
        origin=pts[lines[members[0]][0]]
        origins[name]=origin;body_lines[name]=members
        shapes=[]
        for ln in members:
            pa,pb=lines[ln]
            def local(key):
                return [pts[key][i]-origin[i] for i in (0,1)]
            span=distance(pts[pa],pts[pb])
            shapes.append({"kind":"segment","a":local(pa),"b":local(pb),
                           "thickness":min(.03,max(.0015,.05*span))})
        bodies.append({"id":name,"seed":[*origin,0.],"shapes":shapes})
    for line in lines:
        if line not in owners and not any(r["id"]==line and r.get("construction")=="1"
                                          for r in table["lines"]):
            fail("LINHA_NAO_ATRIBUIDA")
    body_by_original={b["id"]:b["id"].lower() for b in table["bodies"]}
    source_joints=[]
    converted=[]
    for j in table["joints"]:
        k=j["type"]
        if k not in ("revolute","pin_in_slot"):fail("TIPO_JUNTA_NAO_SUPORTADO")
        if j["body_a"]!="ground" and j["body_a"] not in body_by_original:
            fail("CORPO_JUNTA")
        if j["body_b"]!="ground" and j["body_b"] not in body_by_original:
            fail("CORPO_JUNTA")
        a=body_by_original.get(j["body_a"],"ground")
        b=body_by_original.get(j["body_b"],"ground")
        if a==b:fail("AUTO_JUNTA")
        p=j["point"]
        if p not in pts:fail("PIVO_INEXISTENTE")
        def haspoint(body,point):
            if body=="ground":
                return (any(r["id"]==point and r.get("fixed")=="1"
                            for r in table["points"])
                        or any(point in lines[line] and line not in owners
                               for line in lines))
            return any(point in lines[line] for line in body_lines[body])
        def local_xy(body,point):
            origin=origins.get(body,(0.,0.))
            return [pts[point][i]-origin[i] for i in (0,1)]
        if k=="revolute":
            if not haspoint(a,p) or not haspoint(b,p):fail("PIVO_SEM_CORPO")
            converted.append({"kind":"pin","a":a,"b":b,
                              "pa":local_xy(a,p),"pb":local_xy(b,p)})
        else:
            # Upstream convention: body_a owns the slotted LINE,
            # body_b owns the pin POINT; solver convention reversed.
            line=j["line"]
            if not line or line not in lines or (
                  (a!="ground" and owners.get(line)!=a) or
                  (a=="ground" and line in owners)):
                fail("RASGO_SEM_CORPO")
            if not haspoint(b,p):fail("PINO_SEM_CORPO")
            p1,p2=lines[line];start=pts[p1];end=pts[p2]
            vx=end[0]-start[0];vy=end[1]-start[1];length=math.hypot(vx,vy)
            if length<1e-5:fail("RASGO_CURTO")
            proj=((pts[p][0]-start[0])*vx+(pts[p][1]-start[1])*vy)/length**2
            # An explicitly drawn SLOT on a moving link is finite.
            # A ground CONSTRUCTION line is a guide axis; its endpoints
            # are sketch helpers, NOT physical rail end stops.
            is_guide=(a=="ground" and any(
                rr["id"]==line and rr.get("construction")=="1"
                for rr in table["lines"]))
            if not is_guide and not -.000001<=proj<=1.000001:
                fail("PINO_FORA_RASGO_NA_ORIGEM")
            converted.append({"kind":"slot","a":b,"b":a,
                "pa":local_xy(b,p),"pb":local_xy(a,p1),
                "axis_b":[vx/length,vy/length]})
        source_joints.append({
            "source_joint_id":j["id"],"source_type":k,
            "source_pin_point_id":p,
            "source_slot_line_id":j["line"] or None,
            "source_body_a":j["body_a"],"source_body_b":j["body_b"],
            "solver_joint_index":len(converted)-1,
            "finite_slot_length_m":(
                length if k=="pin_in_slot" and not is_guide else None),
            "source_line_is_infinite_construction_guide":(
                bool(is_guide) if k=="pin_in_slot" else False),
        })
    dr=kv(table["driver"])
    if dr.get("type")!="rotary" or dr.get("line_ref") or dr.get("return") not in ("0",""):
        fail("DRIVER_NAO_SUPORTADO")
    line=dr.get("line")
    if line not in owners:fail("DRIVER_SEM_CORPO")
    if dr.get("start") or dr.get("end"):fail("SWEEP_PARCIAL_NAO_SUPORTADO")
    rpm=num(dr.get("speed",""))
    if not 0<rpm<=200:fail("VELOCIDADE")
    omega=2*math.pi*rpm/60
    if omega>25:fail("ACIONADOR_FORA_LIMITE_SOLVER")
    duration=max(2.,60/rpm)
    if duration>12:fail("DURACAO_LONGA")
    # Body local origin is the first source segment point. Initial body
    # orientation is zero; the source sketch coordinates supply the pose.
    spec={
      "schema":S.SCHEMA,"units":"m","ground":{"id":"ground","pose":[0.,0.,0.]},
      "duration_s":duration,"publish":False,"visual_approved":False,
      "bodies":bodies,"joints":converted,
      "driver":{"body":owners[line],"theta0":0.,"speed":omega},
    }
    S.validate(spec)
    return spec,{
        "source_geometry_satisfied_constraints":verified_constraints,
        "source_dimensions_unit":unit,
        "source_driver_rpm":rpm,
        "source_driver_line_id":line,
        "converted_body_count":len(bodies),
        "converted_joint_count":len(converted),
        "joint_provenance":source_joints,
        "driver_from_source":True,
        "body_local_anchors_derived_from_source":True,
        "unverified_body_shapes_rendered":True,
        "source_loads_simulated":False,
        "no_new_solver":True,"no_mechanism_name_dispatch":True,
        "mechanism_source_authoring":"third_party_csv_not_from_natural_language",
    }

def finite_slots(spec,frames,provenance):
    """CSV line is finite; E1 mathematical slot alone describes an infinite line."""
    slots=[p for p in provenance["joint_provenance"]
           if p["source_type"]=="pin_in_slot" and
              p["finite_slot_length_m"] is not None]
    minimum=1.;maximum=0.
    for f in frames:
        for j in slots:
            item=spec["joints"][j["solver_joint_index"]]
            pin=S.world(f["poses"][item["a"]],item["pa"])
            start=S.world(f["poses"][item["b"]],item["pb"])
            axis=S.rotate(item["axis_b"],f["poses"][item["b"]][2])
            length=j["finite_slot_length_m"]
            proj=float((pin-start)@axis/length)
            minimum=min(minimum,proj);maximum=max(maximum,proj)
            transverse=abs(float((pin-start)[0]*axis[1]-(pin-start)[1]*axis[0]))
            if not -1e-5<=proj<=1+1e-5 or transverse>1e-6:
                fail("CONTATO_FORA_DO_SEGMENTO")
    return {"finite_slot_projections_min":minimum,
            "finite_slot_projections_max":maximum,
            "finite_slot_proof":True}

def validate_source_run(manifest,source_entry,*,source_bytes=None,
                        license_bytes=None,live=False,samples=181):
    entries=source_manifest(manifest)
    if source_entry not in entries:fail("NAO_CONGELADO")
    # A test-injected byte stream is NOT a live HTTPS recovery.
    if live and (source_bytes is not None or license_bytes is not None):
        fail("FAKE_LIVE")
    lic=license_bytes if license_bytes is not None else fetch_pinned("LICENSE")
    src=source_bytes if source_bytes is not None else fetch_pinned(source_entry["path"])
    if git_blob_sha1(lic)!=manifest["upstream_license_git_blob_sha1"] or (
       not lic.decode("utf-8").startswith("MIT License")):
        fail("LICENCA_DIVERGIU")
    if git_blob_sha1(src)!=source_entry["blob_sha1"]:
        fail("HASH_DIVERGIU")
    base={
        "schema":"coringa-e7-geometry-import-audit-v1",
        "source_repo":REPOSITORY,"source_commit":COMMIT,
        "source_path":source_entry["path"],
        "source_git_blob_sha1":git_blob_sha1(src),
        "source_sha256":hashlib.sha256(src).hexdigest(),
        "license":"MIT","license_git_blob_sha1":git_blob_sha1(lic),
        "license_verified":True,"source_author":"upstream_developers",
        "source_https_verified_in_ci":bool(live),
        "source_is_machine_readable_csv":True,
        "source_is_not_an_industrial_cad":True,
        "spec_from_human_coded_mechanism_template":False,
        "human_authored_csv_geometry_upstream":True,
        "automated_source_to_solver_spec":False,
        "visual_approved":False,"publish":False,
    }
    try:
        spec,details=source_geometry(src)
        frames=S.trajectory(spec,samples)
        finite=finite_slots(spec,frames,details)
        return {
            **base,"status":"PASS_SOURCE_GEOMETRY_SOLVER_ONLY",
            "trajectory_frames":len(frames),
            "max_residual_m":max(f["max_residual_m"] for f in frames),
            "min_jacobian_rank":min(f["jacobian_rank"] for f in frames),
            "full_rank":all(f["jacobian_rank"]==f["jacobian_size"] for f in frames),
            **details,**finite,
        },spec,frames
    except ValueError as err:
        return {
            **base,"status":"BLOCKED_"+str(err)[:110],
            "geometry_from_source_accepted":False,
            "render_allowed":False,
            "source_to_spec_accepted":False,
        },None,None

def cli():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("out",type=Path)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text("utf8"))
    source_manifest(manifest)
    args.out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for source in manifest["files"]:
        report,spec,frames=validate_source_run(manifest,source,live=args.live)
        reports.append(report)
        safe=Path(source["path"]).stem.replace("-","_")
        if spec:
            (args.out/(safe+"_E7_SPEC.json")).write_text(
                 json.dumps(spec,ensure_ascii=False,indent=2),encoding="utf8")
        (args.out/(safe+"_E7_AUDIT.json")).write_text(
             json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
        print(json.dumps({"source":source["path"],"status":report["status"],
                          "frames":report.get("trajectory_frames",0)},ensure_ascii=False))
    summary={
        "schema":"coringa-e7-import-summary-v1",
        "upstream_repo":REPOSITORY,"upstream_commit":COMMIT,
        "source_cases":reports,
        "passed":sum(x["status"].startswith("PASS") for x in reports),
        "blocked":sum(x["status"].startswith("BLOCKED") for x in reports),
        "network_reported_live":bool(args.live),
        "new_solver_written":False,
        "used_human_source_csv_geometry":True,
        "from_unstructured_web_text":False,
        "images_copied":False,"source_rights":"MIT_verified",
        "automatic_original_mechanism_designed":False,
        "automatic_discovery_from_topic":False,
        "source_to_solver_convert_only":True,
        "art_approved":False,"publish":False,
    }
    (args.out/"QA_E7_GEOMETRY.json").write_text(
         json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"passed":summary["passed"],"blocked":summary["blocked"],
                      "source_to_solver_convert_only":True,"publish":False}))
if __name__=="__main__":
    cli()
