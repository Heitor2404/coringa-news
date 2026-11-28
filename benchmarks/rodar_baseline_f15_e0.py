"""E0 baseline: actually ask legacy F15 to identify all 12 frozen mechanisms.

Inputs are independent hand-encoded minimal topology probes, NOT extracted
from images, URLs, or an LLM. A pass here would only prove topology admission,
not physically correct animation. Never alter frozen target list in this run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from src.v4.formatos import compilador_topologia_f15 as LEGACY

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"benchmarks/generalizacao_mecanismos_v1.json"
PROBES=ROOT/"benchmarks/probes_f15_v1.json"

def measure():
    frozen_bytes=FROZEN.read_bytes()
    probes_bytes=PROBES.read_bytes()
    frozen=json.loads(frozen_bytes)
    supplied=json.loads(probes_bytes)
    if frozen["schema"]!="coringa-generalization-benchmark-v1" or supplied["schema"]!="coringa-f15-structural-probes-v1":
        raise ValueError("E0-BENCHMARK-SCHEMA")
    ids=[x["id"] for x in frozen["targets"]]
    if len(ids)!=12 or set(ids)!=set(supplied["probes"]):
        raise ValueError("E0-BENCHMARK-IDS")
    rows=[]
    for target in frozen["targets"]:
        name=target["id"]
        request={"schema":LEGACY.SCHEMA,"id":name,"title":"MECANISMO TESTADO",
                 "subtitle":"BENCHMARK E0 TOPOLÓGICO","graph":supplied["probes"][name],
                 "required_events":["movimento"],"parameters":{},
                 "evidence":{},"publish":False,"visual_approval":False}
        try:
            family,_,_=LEGACY.identify(request)
            result={"status":"ADMITTED_ONLY_NOT_PHYSICALLY_PROVEN",
                    "family":family,"level":0}
        except ValueError as exc:
            result={"status":"BLOCKED",
                    "reason":str(exc),"level":0}
        rows.append({"id":name,"category":target["category"],
                     "holdout":target["holdout"],**result,
                     "video_rendered":False,"autonomous_spec_generated":False})
    return {
       "schema":"coringa-f15-baseline-observed-v1",
       "benchmark_sha256":hashlib.sha256(frozen_bytes).hexdigest(),
       "probes_sha256":hashlib.sha256(probes_bytes).hexdigest(),
       "method":"MANUAL_MINIMAL_GRAPHS_TO_EXISTING_F15_IDENTIFY_NOT_SOURCE_EXTRACTION",
       "total":len(rows),
       "blocked":sum(x["status"]=="BLOCKED" for x in rows),
       "admitted_not_validated":sum(x["status"]!="BLOCKED" for x in rows),
       "score_ge_3":0,
       "visual_level_4":0,
       "rendering_attempted":False,
       "publication_allowed":False,
       "limitations":"This baseline verifies F15 graph admission, not physics, automatic understanding, CAD or visuals.",
       "cases":rows
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    outcome=measure()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(outcome,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"total":outcome["total"],"blocked":outcome["blocked"],
                      "score_ge_3":outcome["score_ge_3"]}))
