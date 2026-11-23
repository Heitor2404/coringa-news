"""E12: second-source MIT planar joints JSON -> generic E1 poses and 2D shape centers.

No title dispatch, no family-specific solver, no STL/CAD mesh import.
Geometry and anchors are AUTHOR-SUPPLIED in explicit JSON. Added E1 oscillator
is a general actuator for source-limited angular ranges, not a four-bar oracle.
Flexure STL is intentionally NOT rendered as rigid parts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import ssl
from pathlib import Path
from urllib.request import Request,build_opener,HTTPSHandler

from src.v4.formatos import solver_restricoes_e1 as S
from src.v4.formatos.importador_geometria_e7 import git_blob_sha1
from src.v4.formatos.ingestao_evidencias_f16 import NoRedirect

SCHEMA="coringa-e12-independent-planar-json-v1"
REPO="MeghRaval30/compliant-linkage-toolkit"
COMMIT="bb6137456a04d9afaa51240e9fc3e8540d269532"
HOST="https://raw.githubusercontent.com"
SHA=re.compile(r"^[a-f0-9]{40}$")
PATH=re.compile(r"^examples/(?:designs/)?[a-z0-9_]+\.json$")
NAME=re.compile(r"^[a-z][a-z0-9_]{0,39}$")
MAX_BYTES=22000

def fail(reason):
    raise ValueError("E12-SOURCE-"+reason)

def validate_manifest(manifest):
    if (not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA
        or manifest.get("source_repository")!=REPO
        or manifest.get("source_commit")!=COMMIT
        or manifest.get("source_license")!="MIT"
        or manifest.get("source_license_path")!="LICENSE"
        or not SHA.fullmatch(manifest.get("source_license_blob_sha1",""))
        or manifest.get("source_unit")!="mm"
        or manifest.get("source_format")!="planar_linkage_bodies_joints_json"
        or manifest.get("publish") is not False):
        fail("MANIFEST")
    files=manifest.get("files")
    if not isinstance(files,list) or len(files)!=4:fail("FILES")
    paths=set()
    for f in files:
        if (not isinstance(f,dict) or set(f)!={"path","blob_sha1","group"}
           or not isinstance(f["path"],str) or not PATH.fullmatch(f["path"])
           or not isinstance(f["blob_sha1"],str) or not SHA.fullmatch(f["blob_sha1"])
           or f["path"] in paths):
            fail("FILE_ID_OR_HASH")
        paths.add(f["path"])
    return files

def fetch(path):
    if path!="LICENSE" and not PATH.fullmatch(path):
        fail("UNSAFE_PATH")
    url=f"{HOST}/{REPO}/{COMMIT}/{path}"
    req=Request(url,headers={
       "User-Agent":"CoringaE12Lab/1.0 (+github.com/Heitor2404/coringa-news)",
       "Accept":"text/plain","Accept-Encoding":"identity"})
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req,timeout=15) as response:
            if response.status!=200 or response.url!=url:
                fail("REDIRECT")
            raw=response.read(MAX_BYTES+1)
    except (OSError,TimeoutError) as exc:
        fail("FETCH_"+type(exc).__name__)
    if not raw or len(raw)>MAX_BYTES:fail("SIZE")
    return raw

def pt(raw):
    if (not isinstance(raw,list) or len(raw)!=2 or
        any(type(x) not in (float,int) or not math.isfinite(x)
            for x in raw)):
        fail("POINT")
    if max(abs(x) for x in raw)>100000:fail("POINT_RANGE")
    return [float(x)*.001 for x in raw]

def build_spec(source):
    if type(source) is bytes:
        try:source=json.loads(source.decode("utf-8"))
        except (ValueError,UnicodeDecodeError):fail("INVALID_JSON")
    if not isinstance(source,dict):fail("ROOT")
    bodyrows=source.get("bodies")
    rows=source.get("joints")
    if (not isinstance(bodyrows,list) or not 3<=len(bodyrows)<=12
       or not isinstance(rows,dict) or not 3<=len(rows)<=40):
        fail("TOPOLOGY")
    ids=[];ground=[]
    for b in bodyrows:
        if (not isinstance(b,dict) or set(b)!={"name","is_ground"}
            or not isinstance(b["name"],str) or not NAME.fullmatch(b["name"])
            or type(b["is_ground"]) is not bool or b["name"] in ids):
            fail("BODY")
        ids.append(b["name"])
        if b["is_ground"]:ground.append(b["name"])
    if len(ground)!=1:fail("GROUND")
    root=ground[0]
    joints=[];ends={id:[] for id in ids}
    for joint_id,r in rows.items():
        if not isinstance(joint_id,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,16}",joint_id):
            fail("JOINT_ID")
        if (not isinstance(r,dict) or
            not {"bodies","xy_mm","kind"}<=set(r) or
            r["kind"]!="revolute" or
            not isinstance(r["bodies"],list) or len(r["bodies"])!=2):
            fail("UNSUPPORTED_JOINT")
        a,b=r["bodies"]
        if a not in ends or b not in ends or a==b:fail("JOINT_REFERENCES")
        position=pt(r["xy_mm"])
        ends[a].append((joint_id,position));ends[b].append((joint_id,position))
        joints.append((joint_id,a,b,position))
    if any(len(ends[x])<2 for x in ids if x!=root):
        fail("BODY_WITHOUT_TWO_ANCHORS")
    if len(ends[root])<2:fail("GROUND_WITHOUT_TWO_ANCHORS")
    # Reject source graphs not connected to ground; E1 solver will
    # independently reject under/overconstrained topologies and singulars.
    connected={root}
    while True:
        nxt=connected.copy()
        for _,a,b,_ in joints:
            if a in connected:nxt.add(b)
            if b in connected:nxt.add(a)
        if nxt==connected:break
        connected=nxt
    if connected!=set(ids):fail("DISCONNECTED")
    # Anchors are source coordinates at t=0. Every moving part local origin
    # is its first joint, hence seed pose is a world translation with zero
    # rotation. No CAD contour or housing dimensions are implied.
    origin={root:[0.,0.]}
    bodies=[]
    for b in ids:
        if b==root:continue
        anchor_list=ends[b]
        origin[b]=anchor_list[0][1]
        parts=[]
        # For n>=3, join each anchor to the same first anchor. This is
        # illustrative SOURCE centerline topology, not manufacturing plate.
        for _,target in anchor_list[1:]:
            start=anchor_list[0][1]
            if math.dist(start,target)<1e-6:fail("ZERO_LINK_SPAN")
            parts.append({"kind":"segment","a":[0.,0.],
                          "b":[target[0]-start[0],target[1]-start[1]],
                          "thickness":.004})
        bodies.append({"id":b,"seed":[*origin[b],0.],"shapes":parts})
    converted=[]
    provenance=[]
    for jid,a,b,coord in joints:
        converted.append({
          "kind":"pin","a":a,"b":b,
          "pa":[coord[i]-origin[a][i] for i in range(2)],
          "pb":[coord[i]-origin[b][i] for i in range(2)]})
        provenance.append({"joint_id":jid,"bodies":[a,b],
             "source_world_xy_m":coord,"kinematics":"revolute",
             "provenance":"verified_pinned_JSON_field",
             "no_joint_housing_dimensions":True})
    driver_joint=source.get("input_joint")
    if driver_joint not in rows:fail("INPUT_JOINT_UNKNOWN")
    j=next(j for j in joints if j[0]==driver_joint)
    pair=[j[1],j[2]]
    if root not in pair:fail("INPUT_NOT_GROUNDED")
    moving=pair[0] if pair[1]==root else pair[1]
    other_candidates=[p for jid,p in ends[moving] if jid!=driver_joint]
    if len(other_candidates)!=1:
        fail("INPUT_DIRECTION_AMBIGUOUS")
    pivot=j[3]; q=other_candidates[0]
    measured=math.degrees(math.atan2(q[1]-pivot[1],q[0]-pivot[0]))
    meta=source.get("meta")
    bounds=source.get("input_range_deg")
    if (not isinstance(meta,dict)
        or type(meta.get("reference_input_deg")) not in (int,float)
        or not math.isfinite(meta["reference_input_deg"])
        or type(bounds) is not list or len(bounds)!=2
        or any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds)):
        fail("SOURCE_DRIVER_RANGE")
    reference=float(meta["reference_input_deg"])
    error=(measured-reference+180)%360-180
    if abs(error)>1e-3:fail("SOURCE_REFERENCE_ANGLE_MISMATCH")
    low,high=map(float,bounds)
    if not (-360<low<reference<high<360) or high-low>=175:
        fail("SOURCE_RANGE_NOT_OSCILLATORY")
    min_local=math.radians(low-reference);max_local=math.radians(high-reference)
    mid=(min_local+max_local)/2;amplitude=(max_local-min_local)/2
    x=(0-mid)/amplitude
    if abs(x)>1+1e-10:fail("SOURCE_REFERENCE_NOT_IN_RANGE")
    phase=math.acos(max(-1.,min(1.,x)))
    duration=3.0
    driver={"body":moving,"theta0":0.,"speed":2*math.pi/duration,
      "profile":{"kind":"oscillating","range_min_rad":min_local,
                 "range_max_rad":max_local,"phase_rad":phase}}
    spec={
      "schema":S.SCHEMA,"units":"m",
      "ground":{"id":root,"pose":[0.,0.,0.]},
      "bodies":bodies,"joints":converted,
      "driver":driver,"duration_s":duration,
      "visual_approved":False,"publish":False}
    S.validate(spec)
    # Independent exact geometry check at the source reference angle.
    frame=S.solve_one(spec,0.)
    for j in converted:
        a=frame["poses"][j["a"]];b=frame["poses"][j["b"]]
        if math.dist(S.world(a,j["pa"]),S.world(b,j["pb"]))>1e-7:
            fail("SOURCE_TO_SOLVER_JOINT_MISMATCH")
    return spec,{
      "body_count_source":len(ids),
      "moving_body_count":len(bodies),
      "source_joint_count":len(joints),
      "input_joint_id":driver_joint,
      "input_source_reference_deg":reference,
      "input_source_range_deg":[low,high],
      "input_ref_match_deg":error,
      "oscillator_source_range_not_hardcoded":True,
      "sourced_joint_locations":provenance,
      "source_representation":"revolute_linkage_kinematics_only",
      "real_CAD_part_contours_imported":False,
      "compliant_flexure_mesh_rigid_animation_disallowed":True,
    }

def audit_manifest(manifest,*,downloader=fetch,network_verified=False,samples=121):
    files=validate_manifest(manifest)
    if network_verified and downloader is not fetch:
        fail("FAKE_LIVE")
    lic=downloader("LICENSE")
    if (git_blob_sha1(lic)!=manifest["source_license_blob_sha1"]
        or not lic.startswith(b"MIT License")):
        fail("LICENSE_BLOB")
    out=[];valid_specs={}
    for f in files:
        data=downloader(f["path"])
        if git_blob_sha1(data)!=f["blob_sha1"]:
            fail("SOURCE_BLOB")
        record={"source_path":f["path"],"source_blob_sha1":f["blob_sha1"],
                "source_sha256":hashlib.sha256(data).hexdigest(),
                "source_commit":COMMIT,
                "license_verified":True,"source_live":bool(network_verified),
                "source_provenance_verified":True,"publish":False}
        try:
            spec,details=build_spec(data)
            frames=S.trajectory(spec,samples)
            record.update({
              "status":"PASS_SOURCE_JSON_TO_COMMON_SOLVER",
              "frame_count":len(frames),
              "max_residual_m":max(x["max_residual_m"] for x in frames),
              "jacobian_full_rank":all(x["jacobian_rank"]==x["jacobian_size"] for x in frames),
              "source_to_spec_accepted":True,
              **details})
            valid_specs[f["path"]]=spec
        except ValueError as ex:
            record.update({"status":"BLOCKED_"+str(ex)[:140],
                           "source_to_spec_accepted":False})
        out.append(record)
    return {"schema":"coringa-e12-second-origin-kinematics-v1",
       "source_repository":REPO,"source_commit":COMMIT,
       "license":"MIT",
       "license_raw_has_placeholder_author":b"TODO-TEAM-NAME" in lic,
       "license_preserved":True,
       "second_independent_author":True,
       "tested_files":len(out),
       "passed":len(valid_specs),"blocked":len(out)-len(valid_specs),
       "source_cases":out,
       "specs_origin":"author_written_explicit_joint_coordinates",
       "no_source_to_spec_from_prose_or_video":True,
       "no_CAD_contours_attached":True,
       "compliant_STL_not_reused_as_rigid_links":True,
       "real_industrial_machine_verified":False,
       "visual_approved":False,"publish":False}, valid_specs, lic

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text("utf8"))
    report,specs,lic=audit_manifest(manifest,network_verified=True)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"UPSTREAM_MIT_LICENSE.txt").write_bytes(lic)
    for path,spec in specs.items():
        key=Path(path).stem
        (args.out/(key+"_E12_SPEC.json")).write_text(
            json.dumps(spec,ensure_ascii=False,indent=2),encoding="utf8")
    (args.out/"QA_E12_SOURCE_JSON.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"tested":report["tested_files"],"passed":report["passed"],
       "blocked":report["blocked"],"no_CAD_shapes":True},ensure_ascii=False))
if __name__=="__main__":main()
