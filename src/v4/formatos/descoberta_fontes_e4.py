"""E4 laboratory: bounded public encyclopedia discovery with revision-level provenance.

Uses the documented MediaWiki Action API search, then independently fetches
plain page text by pageid and revision. Search snippets NEVER count as evidence.
Public encyclopedic descriptions are not machine design drawings, licenses or
manufacturing dimensions. No automatic MechanismSpec, renderer or publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPSHandler

from src.v4.formatos import relacoes_com_evidencia_f17 as REL
from src.v4.formatos import ingestao_evidencias_f16 as F16

ENDPOINT="https://en.wikipedia.org/w/api.php"
QUERY=re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-]{3,79}$")
WORDS=re.compile(r"[a-z0-9]+")
MENTIONS=("hinge","joint","pin","slide","sliding","meshes","gear","crank",
          "rocker","actuat","rotat","stroke","pivot","reciprocat","ratchet",
          "drive","linkage","return","radius","diameter","length")
NUMBER=re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(millimetres?|millimeters?|"
                  r"centimetres?|centimeters?|meters?|metres?|mm|cm|inches|inch|"
                  r"degrees)(?![A-Za-z])",re.I)
TOKEN=re.compile(r"\b(?:the|and|for|from|mechanism|linkage|machine|system|a|of)\b")
STRUCTURE=re.compile(
    r"\b(?P<count>zero|one|two|three|four|five|six|seven|eight|nine|ten|\d{1,3})"
    r"\s+(?P<part>degrees? of freedom|joints?|bodies|bars|links?|"
    r"turning pairs?|sliding pairs?|pivots?|gears?|shafts?|teeth)\b",re.I)
NUMBER_WORDS={"zero":0,"one":1,"two":2,"three":3,"four":4,
              "five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
MAX_RESULTS=4
MAX_PAGES=2
MAX_BYTES=600000
MAX_TEXT=150000

def fail(code):raise ValueError("E4-FONTE-"+code)

class NoRedirect(F16.NoRedirect):
    pass

def _get_json(params):
    """Only fixed origin and fixed API path; no cross-domain fetch or redirect."""
    url=ENDPOINT+"?"+urlencode(params)
    req=Request(url,headers={
        "User-Agent":"CoringaResearchLab/0.4 (research; https://github.com/Heitor2404/coringa-news)",
        "Accept":"application/json","Accept-Encoding":"identity"})
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    with opener.open(req,timeout=9) as response:
        if response.status!=200 or response.url!=url:fail("HTTP_OU_REDIRECT")
        mime=response.headers.get("content-type","").split(";")[0].strip().lower()
        if mime not in ("application/json","application/vnd.wikimedia+json"):
            fail("MIME")
        body=response.read(MAX_BYTES+1)
    if len(body)>MAX_BYTES:fail("TAMANHO")
    try:data=json.loads(body.decode("utf8"))
    except (ValueError,UnicodeDecodeError):fail("JSON")
    if not isinstance(data,dict) or data.get("error"):fail("API")
    return data

def validate_query(query):
    if not isinstance(query,str) or not QUERY.fullmatch(query) or len(query.split())>8:
        fail("CONSULTA")
    return query.strip()

def search(query,*,get_json=_get_json):
    query=validate_query(query)
    result=get_json({"action":"query","list":"search","srnamespace":"0",
            "srsearch":query,"srlimit":str(MAX_RESULTS),"format":"json",
            "formatversion":"2"})
    hits=result.get("query",{}).get("search")
    if not isinstance(hits,list) or len(hits)>MAX_RESULTS:fail("BUSCA_SCHEMA")
    observed=set();ordered=[]
    for h in hits:
        if not isinstance(h,dict) or h.get("ns")!=0:continue
        p=h.get("pageid");title=h.get("title")
        if type(p) is not int or p<=0 or p in observed:continue
        if not isinstance(title,str) or not 1<=len(title)<=160:continue
        observed.add(p)
        ordered.append({"pageid":p,"title":title})
    # Topic overlap is general, not hardcoded by mechanism family or URL.
    qterms=set(WORDS.findall(query.casefold()))
    qterms={x for x in qterms if len(x)>2}
    ordered.sort(key=lambda h:(-len(qterms & set(WORDS.findall(h["title"].casefold()))),
                               -len(qterms.intersection(WORDS.findall(h["title"].casefold()))),
                               h["pageid"]))
    return ordered[:MAX_PAGES]

def fetch_page(hit,*,get_json=_get_json):
    if not isinstance(hit,dict) or set(hit)!={"pageid","title"} or (
       type(hit["pageid"]) is not int or hit["pageid"]<=0):
        fail("HIT")
    resp=get_json({"action":"query","prop":"extracts|revisions",
                  "explaintext":"1","rvprop":"ids",
                  "pageids":str(hit["pageid"]),
                  "format":"json","formatversion":"2"})
    pages=resp.get("query",{}).get("pages")
    if not isinstance(pages,list) or len(pages)!=1:fail("PAGINA_SCHEMA")
    p=pages[0]
    if (p.get("pageid")!=hit["pageid"] or p.get("missing")
        or not isinstance(p.get("title"),str)
        or not isinstance(p.get("extract"),str)
        or not isinstance(p.get("revisions"),list)
        or not p["revisions"] or type(p["revisions"][0].get("revid")) is not int):
        fail("PAGINA_NAO_COMPROVADA")
    extracted=p["extract"]
    if not 60<=len(extracted)<=MAX_TEXT:fail("TEXTO_INSUFICIENTE")
    return {
        "pageid":p["pageid"],"revid":p["revisions"][0]["revid"],
        "title":p["title"],"plain_text":extracted,
        "source_url":"https://en.wikipedia.org/wiki/"+quote(p["title"].replace(" ","_"),safe=""),
        "text_sha256":hashlib.sha256(extracted.encode("utf8")).hexdigest(),
    }

def derive_evidence(page,*,verified_network=False):
    """Text evidence is sourced; physical interpretation always requires review."""
    if not isinstance(page,dict) or not all(x in page for x in (
       "pageid","revid","title","plain_text","source_url","text_sha256")):
        fail("PROVENIENCIA")
    value=page["plain_text"]
    if (not isinstance(value,str) or not 60<=len(value)<=MAX_TEXT
        or page["text_sha256"]!=hashlib.sha256(value.encode("utf8")).hexdigest()):
        fail("HASH_TEXTO")
    if type(page["pageid"]) is not int or type(page["revid"]) is not int:
        fail("REVISAO")
    if not page["source_url"].startswith("https://en.wikipedia.org/wiki/"):
        fail("ORIGEM")
    sentences=re.split(r"(?<=[.!?])\s+|\s*\n+\s*",value)
    selected=[]
    for raw in sentences:
        sentence=" ".join(raw.split())
        if not 28<=len(sentence)<=220:continue
        if any(m in sentence.casefold() for m in MENTIONS):
            selected.append(sentence)
        if len(selected)>=12:break
    spans=[{"id":f"w{i+1}","text":s,"supported":True}
           for i,s in enumerate(selected)]
    graph=REL.extract(spans) if spans else None
    measurements=[]
    for span in spans:
        for m in NUMBER.finditer(span["text"]):
            measurements.append({
                "span_id":span["id"],
                "verbatim":m.group(0),
                "number":float(m.group(1)),
                "unit_verbatim":m.group(2),
                "source_sentence":span["text"][:200],
                "role_or_component_proven":False,
                "usable_to_fill_mechanism_spec":False,
            })
            if len(measurements)>=12:break
        if len(measurements)>=12:break
    structure=[]
    for span in spans:
        for m in STRUCTURE.finditer(span["text"]):
            word=m.group("count").casefold()
            count=NUMBER_WORDS.get(word,int(word) if word.isdigit() else -1)
            structure.append({
                "span_id":span["id"],"verbatim":m.group(0),
                "count":count,"component_type_verbatim":m.group("part"),
                "source_sentence":span["text"][:200],
                "which_bodies_or_joints":None,
                "full_topology_or_mounting_verified":False,
                "safe_to_instantiate_joint":False,
            })
            if len(structure)>=12:break
        if len(structure)>=12:break
    relations=(graph["edges"] if graph else [])
    return {
        "source":"MediaWiki_Action_API",
        "source_live_verified":bool(verified_network),
        "pageid":page["pageid"],"revid":page["revid"],"title":page["title"],
        "source_url":page["source_url"],"text_sha256":page["text_sha256"],
        "excerpt_count":len(spans),
        "evidence_spans":spans,
        "candidate_relations":[{"source_edge_id":e["id"],
             "relation":e["joint"],"supported_span_ids":e["supported_span_ids"],
             "relationship_semantics_need_review":True} for e in relations],
        "candidate_quantities":measurements,
        "candidate_structural_counts":structure,
        "encyclopedia_is_not_machine_design":True,
        "visual_assets_copied":False,
        "evidence_mode":"EXTRACTED_FROM_RETRIEVED_PAGE_NOT_SEARCH_SNIPPET",
        "human_review_required":True,
        "excerpts_precurated":False,
        "dimensions_bound_to_specific_joint":False,
        "mechanism_spec_generated":False,
        "render_allowed":False,
        "publish":False,
    }

def discover(query,out_dir,*,get_json=_get_json,real_network=False):
    """A mocked API response may exercise the code; it is NOT external proof."""
    validate_query(query)
    # Test doubles must never be mislabeled as live HTTP source evidence.
    if real_network and get_json is not _get_json:
        fail("MOCK_NAO_E_FONTE_LIVE")
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    audit={"schema":"coringa-e4-public-discovery-audit-v0",
        "query":query,"provider":"en.wikipedia.org MediaWiki Action API",
        "real_network_verified":False,
        "status":"BLOCKED_NOT_FETCHED",
        "search_hits":[],"pages":[],"blocked_pages":[],
        "query_human_supplied":True,"URLs_pre_registered":False,
        "source_to_spec_auto":False,"mechanism_spec_generated":False,
        "human_review_required":True,"render_allowed":False,"publish":False}
    try:
        hits=search(query,get_json=get_json)
        audit["search_hits"]=hits
        for hit in hits:
            try:
                page=fetch_page(hit,get_json=get_json)
                audit["pages"].append(derive_evidence(page,verified_network=real_network))
            except (ValueError,TimeoutError,OSError) as err:
                audit["blocked_pages"].append({
                    "pageid":hit["pageid"],"reason":str(err)[:120]})
        audit["real_network_verified"]=bool(real_network and audit["pages"])
        audit["status"]=("DISCOVERY_VERIFIED_TEXT_ONLY" if audit["real_network_verified"]
                          else "BLOCKED_NO_LIVE_PROVEN_SOURCE" if real_network
                          else "MOCKED_DISCOVERY_NO_LIVE_CLAIM")
    except (ValueError,TimeoutError,OSError) as err:
        audit["status"]="BLOCKED_DISCOVERY_"+type(err).__name__
        audit["search_error"]=str(err)[:180]
    file=out/("E4_"+re.sub(r"[^a-z0-9]+","_",query.casefold())+".json")
    file.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf8")
    return audit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("query");ap.add_argument("output",type=Path)
    ap.add_argument("--live",action="store_true")
    args=ap.parse_args()
    record=discover(args.query,args.output,real_network=args.live)
    print(json.dumps({"query":record["query"],"status":record["status"],
        "verified_pages":len(record["pages"]) if record["real_network_verified"] else 0,
        "automatic_specs":0,"publish":False},ensure_ascii=False))
if __name__=="__main__":main()
