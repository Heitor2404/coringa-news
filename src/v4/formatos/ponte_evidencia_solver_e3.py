"""E3 laboratory: independently check source-backed joint claims against E1 specs.

A source phrase proves a relationship, NOT numeric dimensions, a CAD drawing,
seeds, axes, complete topology, or permission to publish. The only live pathway
uses F16's HTTPS allowlist + F17's per-span relations. No title-based routing.
No LLM is called here: candidate MechanismSpec is still human-authored.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from src.v4.formatos import ingestao_evidencias_f16 as SOURCE
from src.v4.formatos import relacoes_com_evidencia_f17 as REL
from src.v4.formatos import solver_restricoes_e1 as SOLVER

SCHEMA="coringa-e3-mechanism-evidence-binding-v1"
REPORT_SCHEMA="coringa-e3-source-to-joints-audit-v1"
JOINT_RULES={
    "hinged_to":("pin",("pa","pb")),
    "slides_in":("slider",("pa","pb","axis_a","angle_offset")),
}
HASH=re.compile(r"^[0-9a-f]{64}$")

def fail(code):
    raise ValueError("E3-EVIDENCIA-"+code)

def validate_binding(doc,spec,binding):
    """Check human source-role bindings BEFORE trusting them as citations."""
    SOURCE.validate_document(doc)
    SOLVER.validate(spec)
    if not isinstance(binding,dict) or set(binding)!={
        "schema","source_id","body_roles","joint_claims",
        "spec_authorship","numbers_from_source","publish"
    }:
        fail("CONTRATO")
    if (binding["schema"]!=SCHEMA or binding["source_id"]!=doc["id"] or
        binding["spec_authorship"]!="manual_prototype" or
        binding["numbers_from_source"] is not False or
        binding["publish"] is not False):
        fail("PROCEDENCIA")
    roles=binding["body_roles"]
    if not isinstance(roles,dict) or not roles:
        fail("PAPEIS")
    ids={spec["ground"]["id"]}|{b["id"] for b in spec["bodies"]}
    for a,b in roles.items():
        if not isinstance(a,str) or not a or not isinstance(b,str) or b not in ids:
            fail("PAPEIS")
    claims=binding["joint_claims"]
    if not isinstance(claims,list) or len(claims)>len(spec["joints"]):
        fail("CITACOES")
    indices=set();edges=set()
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!={"joint_index","edge_id"}:
            fail("CITACAO_FORMATO")
        idx=claim["joint_index"]
        if type(idx) is not int or not 0<=idx<len(spec["joints"]):
            fail("INDICE")
        if (idx in indices or not isinstance(claim["edge_id"],str) or
            not claim["edge_id"] or claim["edge_id"] in edges):
            fail("CITACAO_DUPLICADA")
        indices.add(idx);edges.add(claim["edge_id"])
    return True

def joint_candidates(graph):
    """Turns relation IDs into generic constraint sketches, never geometry."""
    result=[]
    for edge in graph["edges"]:
        known=JOINT_RULES.get(edge["joint"])
        result.append({
            "source_edge_id":edge["id"],
            "from":edge["from"],"to":edge["to"],
            "relation":edge["joint"],
            "supported_span_ids":list(edge["supported_span_ids"]),
            "evidence_kind":edge["evidence_kind"],
            "solver_joint_kind":known[0] if known else None,
            "required_manual_geometry":list(known[1]) if known else [],
            "status":"RELATION_ONLY_REQUIRES_DIMENSIONS" if known
                else "UNSUPPORTED_BY_CURRENT_PLANAR_SOLVER",
        })
    return result

def analyze(doc,spec,binding,ledger,*,live_proof=False):
    """ledger must originate from F17 extraction; NEVER a citable live claim by itself.

    Even when live_proof=True (set only by run() HTTPS path), drawings and
    dimensions remain manual and human review is always required.
    """
    validate_binding(doc,spec,binding)
    if not isinstance(ledger,dict) or ledger.get("schema")!=REL.SCHEMA:
        fail("LIVRO_PROVAS")
    if ledger.get("source_id")!=doc["id"] or ledger.get("source_url")!=doc["url"]:
        fail("FONTE_DIFERENTE")
    if live_proof and (ledger.get("source_live_verified") is not True or
                       not isinstance(ledger.get("source_sha256"),str) or
                       not HASH.fullmatch(ledger["source_sha256"])):
        fail("LIVE_NAO_COMPROVADO")
    graph=ledger["graph"]
    edges={e["id"]:e for e in graph["edges"]}
    known_nodes={n["id"] for n in graph["nodes"]}
    if set(binding["body_roles"])-known_nodes:
        fail("PAPEL_SEM_PROVA")
    source_proven=[]
    for claimed in binding["joint_claims"]:
        idx=claimed["joint_index"]
        evidence=edges.get(claimed["edge_id"])
        if evidence is None or not evidence.get("supported_span_ids"):
            fail("ARESTA_INVENTADA")
        relation=evidence["joint"]
        solver_kind=JOINT_RULES.get(relation,(None,))[0]
        j=spec["joints"][idx]
        if solver_kind is None or j["kind"]!=solver_kind:
            fail("TIPO_DE_JUNTA_SEM_PROVA")
        # Preserve orientation: 'piston slides_in chamber' corresponds to
        # 'a=chamber (guide), b=piston (slider)' in E1's constraint convention.
        src=binding["body_roles"].get(evidence["from"])
        dst=binding["body_roles"].get(evidence["to"])
        if src is None or dst is None:
            fail("CORPO_SEM_CORRESPONDENCIA")
        if relation=="slides_in":
            endpoint_ok=j["a"]==dst and j["b"]==src
        else:
            endpoint_ok={j["a"],j["b"]}=={src,dst}
        if not endpoint_ok:
            fail("EXTREMIDADES_INCOMPATIVEIS")
        source_proven.append({
            "joint_index":idx,"solver_kind":j["kind"],
            "relation":relation,"source_edge_id":evidence["id"],
            "supported_span_ids":list(evidence["supported_span_ids"]),
            "relationship_proven":True,
            "dimensions_and_axis_proven":False,
        })
    remaining=sorted(set(range(len(spec["joints"])))-
                     {x["joint_index"] for x in source_proven})
    candidate=joint_candidates(graph)
    # Numeric success is an independent check of a human-authored model.
    # It does NOT turn unsupported relationships into sourced facts.
    try:
        trajectory=SOLVER.trajectory(spec,33)
        physics={
            "status":"PASS_MANUAL_GEOMETRY_ONLY",
            "samples":len(trajectory),
            "max_residual_m":max(f["max_residual_m"] for f in trajectory),
            "all_jacobians_full_rank":all(
                f["jacobian_rank"]==f["jacobian_size"] for f in trajectory),
        }
    except ValueError as exc:
        physics={"status":"FAIL_GEOMETRY","error":str(exc)[:140]}
    no_full_support=bool(remaining)
    status=("BLOCKED_SOURCE_NOT_LIVE" if not live_proof
            else "BLOCKED_UNPROVEN_JOINTS" if no_full_support
            else "BLOCKED_MANUAL_GEOMETRY_REQUIRES_REVIEW")
    if physics["status"]!="PASS_MANUAL_GEOMETRY_ONLY":
        status="BLOCKED_GEOMETRY"
    return {
        "schema":REPORT_SCHEMA,"status":status,
        "source_id":doc["id"],"source_url":doc["url"],
        "source_live_verified":bool(live_proof),
        "source_sha256":ledger.get("source_sha256") if live_proof else None,
        "source_excerpts_checked":ledger.get("source_excerpt_count"),
        "candidate_joints_from_source":candidate,
        "candidate_joints_supported_by_current_solver":sum(
            c["solver_joint_kind"] is not None for c in candidate),
        "human_authored_spec":True,
        "body_bindings_human_authored":True,
        "geometry_values_source_verified":False,
        "source_supported_joint_claims":source_proven,
        "joint_claims_supported":len(source_proven),
        "joint_claims_total":len(spec["joints"]),
        "unproven_joint_indices":remaining,
        "unsupported_source_relation_ids":[c["source_edge_id"]
             for c in candidate if c["solver_joint_kind"] is None],
        "geometry_preflight":physics,
        "source_to_complete_spec_automatic":False,
        "human_review_required":True,"render_allowed":False,
        "visual_approved":False,"publish":False,
    }

def run(doc_path,spec_path,binding_path,out_dir,*,live=False):
    """One closed source transport; mocked fixtures are not evidence of live GET."""
    doc=SOURCE.load_document(doc_path)
    spec=json.loads(Path(spec_path).read_text("utf8"))
    binding=json.loads(Path(binding_path).read_text("utf8"))
    validate_binding(doc,spec,binding)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    base={
        "schema":REPORT_SCHEMA,"source_id":doc["id"],"source_url":doc["url"],
        "status":"BLOCKED_NO_LIVE_SOURCE","source_live_verified":False,
        "source_to_complete_spec_automatic":False,"human_review_required":True,
        "render_allowed":False,"visual_approved":False,"publish":False,
    }
    record=base
    if live:
        try:
            fetched=SOURCE.fetch_html(doc["url"])
            if fetched["final_url"]!=doc["url"]:fail("REDIRECT")
            audited=REL.audit_verified_source(
                doc,fetched["text"],source_sha256=fetched["raw_sha256"],
                proof_from_https=True)
            record=analyze(doc,spec,binding,audited,live_proof=True)
            record["source_mime"]=fetched["mime"]
        except (ValueError,OSError) as exc:
            record=dict(base)
            record["status"]="BLOCKED_SOURCE_OR_CONTRACT_"+type(exc).__name__
            record["source_error"]=str(exc)[:180]
    dest=out/(doc["id"]+"_E3_AUDIT.json")
    dest.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf8")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path);p.add_argument("spec",type=Path)
    p.add_argument("bindings",type=Path);p.add_argument("output",type=Path)
    p.add_argument("--live",action="store_true")
    args=p.parse_args()
    result=run(args.manifest,args.spec,args.bindings,args.output,live=args.live)
    print(json.dumps({
        "status":result["status"],"source":result["source_id"],
        "live":result["source_live_verified"],
        "joint_claims_supported":result.get("joint_claims_supported",0),
        "render_allowed":False,"publish":False
    },ensure_ascii=False))
if __name__=="__main__":main()
