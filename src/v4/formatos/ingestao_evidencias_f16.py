"""F16 — ingestão de trechos técnicos com prova de proveniência, ou bloqueio.

Curadoria dos TRECHOS é humana: a extração de relações é determinística e
limitada. Não faz descoberta aberta, OCR, tradução sem fonte, CAD nem VLM.
Apenas se cada trecho constar no HTML efetivamente recuperado pode habilitar
o pré-voo F15 (NUNCA publicação). Sem resposta da fonte => NÃO CONFIRMADO.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from src.v4.formatos import compilador_topologia_f15 as SELECTOR

SCHEMA="coringa-documentary-evidence-f16-v1"
RECORD_SCHEMA="coringa-evidence-audit-f16-v1"
DIR=Path(__file__).with_name("evidencias_f16")
CANONICAL={
 "https://mechanics.ju.se/MachineElements/spur-gears.html",
 "https://jd-jones-ases.github.io/Mechanic/things/slider-crank/",
 "https://www.ahydraulics.com/en/about-us/frequently-asked-questions/frequently-asked-questions-about-scissor-lifts/how-does-a-scissor-lift-work-hydraulically/",
 "https://hydraproducts.co.uk/hydraulic-power-packs/power-pack-applications/commercial-systems/scissor-lift/",
}

def fail(code):
    raise ValueError("F16-FONTE-"+code)

def norm(value):
    if not isinstance(value,str): fail("TEXTO")
    value=html.unescape(value).casefold().replace("\u00a0"," ")
    return " ".join(re.findall(r"[\w]+",value,flags=re.UNICODE))

class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text=[];self.off=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"):
            self.off+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg"):
            self.off=max(0,self.off-1)
    def handle_data(self,data):
        if not self.off:self.text.append(data)

def page_text(body,content_type):
    if content_type not in ("text/html","application/xhtml+xml","text/plain"):
        fail("TIPO")
    if len(body)>900000 or len(body)<35:
        fail("TAMANHO")
    try:s=body.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("CODIFICACAO")
    if content_type=="text/plain": return s
    parser=TextHTML()
    parser.feed(s)
    return " ".join(parser.text)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        fail("REDIRECIONAMENTO")

def fetch_html(url):
    if url not in CANONICAL: fail("URL_NAO_AUTORIZADA")
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.username or parts.password or parts.port not in (None,443):
        fail("URL_INVALIDA")
    req=urllib.request.Request(url,headers={
        "User-Agent":"CoringaLabEvidenceAudit/0.1 (+https://github.com/Heitor2404/coringa-news)",
        "Accept":"text/html, text/plain;q=0.5","Accept-Encoding":"identity",
    })
    opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req,timeout=9) as response:
            if response.status!=200:fail("HTTP")
            mime=response.headers.get("content-type","").split(";")[0].strip().lower()
            body=response.read(900001)
            if response.headers.get("content-encoding")=="gzip":
                body=gzip.decompress(body)
            value=page_text(body,mime)
            return {"text":value,"raw_sha256":hashlib.sha256(body).hexdigest(),
                    "final_url":response.url,"mime":mime}
    except (TimeoutError,urllib.error.URLError,OSError) as exc:
        fail("DOWNLOAD_INDISPONIVEL_"+type(exc).__name__)

def load_document(path):
    p=Path(path)
    if not p.is_file() or p.suffix!=".json" or p.stat().st_size>13000:
        fail("ARQUIVO")
    try:doc=json.loads(p.read_text("utf8"))
    except (UnicodeError,ValueError):
        fail("JSON")
    validate_document(doc)
    return doc

def validate_document(d):
    if (not isinstance(d,dict) or d.get("schema")!=SCHEMA or
        d.get("url") not in CANONICAL or
        not isinstance(d.get("id"),str) or not SELECTOR.IDENT.fullmatch(d["id"]) or
        d.get("original_media_used") is not False or
        d.get("image_license_claimed") is not False or
        d.get("publication_allowed") is not False or
        d.get("extraction_requires_live_anchor_check") is not True):
        fail("CONTRATO")
    items=d.get("quoted_spans")
    if not isinstance(items,list) or not 2<=len(items)<=5:fail("TRECHOS")
    keys=set()
    for item in items:
        if (not isinstance(item,dict) or set(item)!={"id","locator","text"}
            or not isinstance(item["id"],str) or item["id"] in keys or
            not isinstance(item["locator"],str) or not 3<=len(item["locator"])<=120
            or not isinstance(item["text"],str) or not 5<=len(item["text"])<=160):
            fail("TRECHO_INVALIDO")
        keys.add(item["id"])
    return True

def verified_spans(doc,full_text):
    """Constata presença LITERAL normalizada de cada citação no texto obtido.

    O URL não determina a família; somente os spans sustentam relações.
    """
    validate_document(doc)
    normalized=norm(full_text)
    spans=[]
    for item in doc["quoted_spans"]:
        if norm(item["text"]) not in normalized:
            fail("ANCORA_AUSENTE_"+item["id"])
        spans.append({"id":item["id"],"locator":item["locator"],
                      "text":item["text"],"supported":True})
    return spans

def infer_graph(spans):
    """Extrator limitado por expressões evidenciais, SEM supor peças ocultas."""
    facts=norm(" ".join(x["text"] for x in spans))
    source_ids=[x["id"] for x in spans]
    if all(x in facts for x in ("spur gear", "two gears in mesh turn", "opposite directions")):
        return {
           "kind":"known_spur_pair",
           "nodes":[{"id":"entrada","kind":"spur_gear"},{"id":"saida","kind":"spur_gear"}],
           "edges":[{"from":"entrada","to":"saida","joint":"meshes_with"}],
           "supported_span_ids":source_ids,
           "roles_input_output_deduced_by_engineer":True,
           "events_from_kernel_not_page":["engagement","reduction"],
           "uncertainties":["no_tooth_count_in_text","no_module_in_text",
                            "no_fabrication_tolerance","no_appearance_license"],
        }
    if all(x in facts for x in ("rigid crank and connecting rod",
                                "ideal pin joints",
                                "piston pin slides on the cylinder axis")):
        return {
            "kind":"partial_slider_crank",
            "nodes":[{"id":"manivela","kind":"rotor"},{"id":"haste","kind":"rod"},
                     {"id":"pistao","kind":"piston"},{"id":"camara","kind":"chamber"}],
            "edges":[{"from":"manivela","to":"haste","joint":"hinged_to"},
                     {"from":"haste","to":"pistao","joint":"hinged_to"},
                     {"from":"pistao","to":"camara","joint":"slides_in"}],
            "supported_span_ids":source_ids,
            "uncertainties":["motor_pulley_not_evidenced","belt_not_evidenced",
                             "flywheel_not_evidenced","motion_not_measured"],
        }
    known_hydraulic=(all(x in facts for x in (
         "electric motor drives the pump",
         "pump sends oil to the lift cylinder",
         "pushes the scissor arms upward"))
      or all(x in facts for x in (
         "motor runs the hydraulic pump",
         "pumping hydraulic oil into the hydraulci ram",
         "ram extends the scissors open")))
    if known_hydraulic:
        return {
            "kind":"hydraulic_scissor_lift_UNSUPPORTED",
            "nodes":[{"id":"motor","kind":"electric_motor"},
                     {"id":"bomba","kind":"hydraulic_pump"},
                     {"id":"cilindro","kind":"hydraulic_cylinder"},
                     {"id":"bracos","kind":"scissor_arms"}],
            "edges":[{"from":"motor","to":"bomba","joint":"drives"},
                     {"from":"bomba","to":"cilindro","joint":"fluid_to"},
                     {"from":"cilindro","to":"bracos","joint":"pushes"}],
            "supported_span_ids":source_ids,
            "uncertainties":["no_joint_dimensions","no_hydraulic_kernel",
                             "no_lift_kinematics","no_visual_identity_license"],
        }
    return {
        "kind":"evidence_not_decidable",
        "nodes":[],"edges":[],"supported_span_ids":source_ids,
        "uncertainties":["insufficient_source_claims_for_mechanical_graph"],
    }

def audit(doc,source_text=None,*,origin="unverified"):
    """source_text não é aceito como comprovação LIVE por si só."""
    validate_document(doc)
    result={
       "schema":RECORD_SCHEMA,
       "doc_id":doc["id"],"source_url":doc["url"],
       "source_ownership":"third_party_text",
       "visual_media_used":False,"image_license_proven":False,
       "source_live_verified":False,
       "source_retrieval":"PENDENTE",
       "verified_anchors":[],"candidate_graph":None,
       "f15_preflight_passed":False,"publication_allowed":False,
       "human_review_required":True,
    }
    if source_text is None:
        result["status"]="BLOQUEADO_SEM_HTML_DA_FONTE"
        return result
    spans=verified_spans(doc,source_text)
    result["verified_anchors"]=spans
    result["candidate_graph"]=infer_graph(spans)
    if origin!="live":
        result["source_retrieval"]="TEXT_FIXTURE_NOT_LIVE"
        result["status"]="BLOQUEADO_ORIGEM_NAO_COMPROVADA"
        return result
    result["source_live_verified"]=True
    result["source_retrieval"]="HTTPS_SOURCE_SAME_URL_AND_ANCHORS"
    if result["candidate_graph"]["kind"]=="known_spur_pair":
        result["status"]="EVIDENCIA_PARA_COMPILADOR_CONDICIONAL"
    else:
        result["status"]="BLOQUEADO_TOPOLOGIA_INCOMPLETA_OU_SEM_KERNEL"
    return result

def compile_gear_from_verified(record,spec):
    if (record.get("source_live_verified") is not True
        or record.get("status")!="EVIDENCIA_PARA_COMPILADOR_CONDICIONAL"
        or record.get("candidate_graph",{}).get("kind")!="known_spur_pair"):
        fail("PREVOO_SEM_PROVA_EXTERNA")
    if (not isinstance(spec,dict) or
        set(spec)!={"id","title","subtitle","parameters"}):
        fail("ESPECIFICACAO")
    # Parâmetros são fornecidos pelo projetista, NÃO extraídos dos excertos!
    base=copy.deepcopy(SELECTOR.load_request(
        Path(__file__).with_name("pedidos_topologia_f15")/"pedido_estrutura_engrenagens_f15.json"))
    base["id"],base["title"],base["subtitle"]=spec["id"],spec["title"],spec["subtitle"]
    base["parameters"]=copy.deepcopy(spec["parameters"])
    base["graph"]=copy.deepcopy({
       "nodes":record["candidate_graph"]["nodes"],
       "edges":record["candidate_graph"]["edges"],
    })
    plan=SELECTOR.compile_request(base)
    if plan["compiled_family"]!="external_spur_gear_reduction" or plan["publish"] is not False:
        fail("KERNEL_INCONSISTENTE")
    record["f15_preflight_passed"]=True
    record["status"]="PREVOO_F15_OK_REVISAO_HUMANA_PENDENTE"
    record["physics_kernel_is_distinct_from_source_url"]=True
    record["manual_design_parameters_not_from_reference"]=True
    return plan

def run(docfile,outdir,*,try_live=False,specfile=None):
    doc=load_document(docfile)
    output=Path(outdir);output.mkdir(parents=True,exist_ok=True)
    try:
        downloaded=fetch_html(doc["url"]) if try_live else None
        report=audit(doc,downloaded["text"] if downloaded else None,
                     origin="live" if downloaded else "unverified")
        if downloaded:
            report["raw_source_sha256"]=downloaded["raw_sha256"]
            report["source_mime"]=downloaded["mime"]
            report["resolved_url"]=downloaded["final_url"]
            if downloaded["final_url"]!=doc["url"]:
                fail("URL_FINAL_DIFERENTE")
    except ValueError as exc:
        if not str(exc).startswith("F16-FONTE-"):raise
        report=audit(doc)
        report["status"]="BLOQUEADO_ORIGEM_"+str(exc)
        report["source_error"]=str(exc)
    if report["source_live_verified"] and specfile and report["candidate_graph"]["kind"]=="known_spur_pair":
        try:
            plan=compile_gear_from_verified(report,json.loads(Path(specfile).read_text("utf8")))
            (output/(doc["id"]+"_PLANO_F15.json")).write_text(
                json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf8")
        except (ValueError,OSError,UnicodeError) as exc:
            report["status"]="BLOQUEADO_COMPILACAO_"+type(exc).__name__
            report["compilation_error"]=str(exc)
    # Não arquiva página inteira de terceiros; só trechos curtos de manifesto.
    (output/(doc["id"]+"_AUDITORIA.json")).write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("evidence",type=Path)
    parser.add_argument("out",type=Path)
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--gear-spec",type=Path)
    args=parser.parse_args()
    report=run(args.evidence,args.out,try_live=args.live,specfile=args.gear_spec)
    print(json.dumps({"doc":report["doc_id"],"status":report["status"],
                      "source_live_verified":report["source_live_verified"],
                      "preflight":report["f15_preflight_passed"],
                      "publication_allowed":False},ensure_ascii=False))

if __name__=="__main__":main()
