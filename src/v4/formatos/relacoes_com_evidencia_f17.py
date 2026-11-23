"""F17 — relations with per-edge evidence and an honest kernel-gap plan.

The F16 allowlisted HTTPS downloader is reused.  This module is NOT a general
language model, a VLM, a media importer, or a scissor-lift simulator.

Unlike F16's page-level pattern, independent generic *relation* rules examine
each confirmed excerpt. Evidence is attached to EACH relation separately.
Excerpts that merely name parts cannot magically provide missing joints.
A candidate topology is never a publishing authorization.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from src.v4.formatos import ingestao_evidencias_f16 as SOURCE
from src.v4.formatos import compilador_topologia_f15 as COMPILER

SCHEMA="coringa-relation-ledger-f17-v1"
FORBIDDEN=re.compile(r"\b(?:not|never|without|cannot|does not|do not|no|fails to)\b")
# General vocabulary for relationships. NO source URL or ID appears in these rules.
# Contradictions, directions, and unobserved mounting geometry remain unverified.
RULES=(
    ("motor_pump", "electric_motor", "hydraulic_pump", "drives",
     re.compile(r"\b(?:electric )?motor (?:drives|runs|powers) (?:the )?(?:hydraulic )?pump\b")),
    ("pump_actuator", "hydraulic_pump", "hydraulic_cylinder", "fluid_to",
     re.compile(r"\b(?:pump sends (?:hydraulic )?oil to (?:the )?(?:lift |hydraulic )?cylinder|pump(?:ing|s)? (?:hydraulic )?oil into (?:the )?(?:hydraulci |hydraulic )?ram|(?:hydraulic )?fluid flows from (?:the )?pump to (?:the )?(?:hydraulic |lift )?cylinder)\b")),
    ("actuator_scissors", "hydraulic_cylinder", "scissor_arms", "pushes",
     re.compile(r"\b(?:ram extends the scissors open|(?:hydraulic )?(?:cylinder|ram) pushes (?:the )?scissor arms(?: upward)?|pushes the scissor arms upward)\b")),
    ("gear_mesh", "gear_1", "gear_2", "meshes_with",
     re.compile(r"\b(?:two gears (?:in mesh|mesh with each other)|gears mesh with each other)\b")),
    ("piston_slide", "piston", "chamber", "slides_in",
     re.compile(r"\b(?:piston pin slides on the cylinder axis|piston slides inside (?:the )?cylinder)\b")),
    ("crank_rod_hinge", "crank", "rod", "hinged_to",
     re.compile(r"\b(?:crank (?:is )?hinged to (?:the )?connecting rod|connecting rod (?:is )?pinned to (?:the )?crank)\b")),
    ("rod_piston_hinge", "rod", "piston", "hinged_to",
     re.compile(r"\b(?:connecting rod (?:is )?hinged to (?:the )?piston|connecting rod (?:is )?pinned to (?:the )?piston)\b")),
)
KINDS={
    "electric_motor":"electric_motor","hydraulic_pump":"hydraulic_pump",
    "hydraulic_cylinder":"hydraulic_cylinder","scissor_arms":"scissor_arms",
    "gear_1":"gear","gear_2":"gear","crank":"rotor",
    "rod":"rod","piston":"piston","chamber":"chamber",
}
# Requirements are ENGINEERING WORK TO BE DONE, not facts extracted from a website.
GAP_REQUIREMENTS=(
    {"id":"linkage_geometry",
     "capability":"scissor_linkage_kinematics_2d",
     "inputs_needed":["number_of_stages","arm_lengths","ground_pivots",
                      "moving_platform_constraints","central_pin_positions"],
     "validation":"closure of all pin joints across operating range"},
    {"id":"actuator_mounting",
     "capability":"cylinder_to_scissor_constraint",
     "inputs_needed":["cylinder_fixed_mount","cylinder_moving_mount",
                      "retracted_length","usable_stroke","min_max_platform_height"],
     "validation":"actuator extension corresponds to linkage height without impossible poses"},
    {"id":"hydraulic_circuit",
     "capability":"hydraulic_power_and_control",
     "inputs_needed":["reservoir_and_return","pump_flow","cylinder_area",
                      "pressure_limit","control_and_holding_valves"],
     "validation":"consistent flow and motion; no unproved real-world safety claim"},
    {"id":"visual_identity",
     "capability":"licensed_machine_visual_reference",
     "inputs_needed":["exact_machine_variant","geometry_reference",
                      "asset_permission","attribution_and_modifications"],
     "validation":"reference authenticity, license, human visual review"},
)
TECHNICAL_GAP_CONTEXT=(
    "https://jtambg.eu/papers/2024/JTAM2024_2_232-241.pdf",
    "https://www.ahydraulics.com/en/about-us/frequently-asked-questions/"
    "frequently-asked-questions-about-scissor-lifts/which-hydraulic-components-are-used-in-a-scissor-lift/",
)

def fail(code):
    raise ValueError("F17-PROVA-"+code)

def _id(s):
    if not isinstance(s,str) or not COMPILER.IDENT.fullmatch(s):
        fail("ID")
    return s

def _excerpt_spans(doc,source_html):
    """Every quote must exist on the fetched page; F16 owns that proof."""
    return SOURCE.verified_spans(doc,source_html)

def extract(spans):
    """Build a *candidate* graph from supported per-span relationships.

    Pass only spans verified against the source in the live orchestrator.
    Standalone calls (e.g. unit fixtures) are NOT live source verification.
    """
    if not isinstance(spans,list) or not 1<=len(spans)<=12:
        fail("TRECHOS")
    identifiers=set()
    edges=[]
    nodes={}
    warnings=[]
    for span in spans:
        if not isinstance(span,dict) or set(("id","text","supported"))-span.keys():
            fail("TRECHO")
        sid=_id(span["id"])
        if sid in identifiers or span["supported"] is not True:
            fail("TRECHO_NAO_VERIFICADO")
        identifiers.add(sid)
        norm=SOURCE.norm(span["text"])
        if FORBIDDEN.search(norm):
            warnings.append({"span_id":sid,"reason":"NEGATED_OR_UNCERTAIN_PHRASE_IGNORED"})
            continue
        # A name occurring in an excerpt does NOT prove a mechanical joint.
        if "rigid crank and connecting rod" in norm:
            nodes.setdefault("crank",{"id":"crank","kind":"rotor","supported_span_ids":[]})
            nodes.setdefault("rod",{"id":"rod","kind":"rod","supported_span_ids":[]})
            for key in ("crank","rod"):
                if sid not in nodes[key]["supported_span_ids"]:
                    nodes[key]["supported_span_ids"].append(sid)
        for rule_id,src,dst,joint,pattern in RULES:
            m=pattern.search(norm)
            if not m:
                continue
            for key in (src,dst):
                nodes.setdefault(key,{"id":key,"kind":KINDS[key],"supported_span_ids":[]})
                if sid not in nodes[key]["supported_span_ids"]:
                    nodes[key]["supported_span_ids"].append(sid)
            edges.append({
               "id":rule_id+"_"+sid,"from":src,"to":dst,"joint":joint,
               "supported_span_ids":[sid],"evidence_kind":"direct_lexical_relation",
               "matched_phrase":m.group(0),
               "direction_confirmed":rule_id!="gear_mesh",
            })
    # Do not infer 'spur' from generic gears. Source must explicitly name the kind.
    explicit_spur=[s["id"] for s in spans
                   if s["supported"] is True and "spur gear" in SOURCE.norm(s["text"])
                   and not FORBIDDEN.search(SOURCE.norm(s["text"]))]
    if "gear_1" in nodes and explicit_spur:
        for gear_id in ("gear_1","gear_2"):
            nodes[gear_id]["kind"]="spur_gear"
            for sid in explicit_spur:
                if sid not in nodes[gear_id]["supported_span_ids"]:
                    nodes[gear_id]["supported_span_ids"].append(sid)
    edges.sort(key=lambda e:e["id"])
    order=sorted(nodes)
    families={r["joint"] for r in edges}
    if families and families<=set(("drives","fluid_to","pushes")):
        family="hydraulic_scissor_lift"
    elif families=={"meshes_with"} and all(
          n["kind"]=="spur_gear" for n in nodes.values()):
        family="external_spur_pair"
    elif families and families<=set(("hinged_to","slides_in")):
        family="partial_slider_crank"
    elif not families:
        family="insufficient_explicit_relations"
    else:
        family="mixed_or_unclassified"
    return {
       "family_candidate":family,
       "nodes":[nodes[n] for n in order],
       "edges":edges,
       "warnings":warnings,
       "source_span_ids":sorted(identifiers),
       "no_implicit_edges":True,
       "numeric_geometry_inferred":False,
    }

def _topology_gaps(graph):
    family=graph["family_candidate"]
    if family=="hydraulic_scissor_lift":
        remaining={e["joint"] for e in graph["edges"]}
        required={"drives","fluid_to","pushes"}
        missing=sorted(required-remaining)
        return {
            "status":"BLOCKED_NO_KERNEL",
            "unproven_expected_relations":missing,
            "new_node_kinds":sorted({n["kind"] for n in graph["nodes"]}-
                                    COMPILER.NODE_KINDS),
            "new_edge_kinds":sorted({e["joint"] for e in graph["edges"]}-
                                    COMPILER.LINK_KINDS),
            "required_subsystems":copy.deepcopy(GAP_REQUIREMENTS),
            "research_context_not_live_verified_in_this_run":list(TECHNICAL_GAP_CONTEXT),
            "industrial_drawings_imported":False,
            "is_machine_design_complete":False,
        }
    if family=="partial_slider_crank":
        required=[
           ("motor_pulley","drive_belt","drives"),
           ("drive_belt","flywheel","transmits_to"),
           ("flywheel","connecting_rod","hinged_to"),
           ("connecting_rod","piston","hinged_to"),
        ]
        return {
          "status":"BLOCKED_MISSING_JOINTS_AND_COMPONENTS",
          "unproven_required_connections":[{"from":a,"to":b,"joint":c}
                                           for a,b,c in required],
          "source_is_partial":True,"render_allowed":False,
        }
    if family=="external_spur_pair":
        return {
          "status":"STRUCTURE_RECOGNIZED_DESIGNER_BINDING_REQUIRED",
          "unknown_input_output_orientation":True,
          "tooth_counts_observed":False,
          "module_observed":False,
          "source_only_proves_mesh_not_design_values":True,
          "render_allowed":False,
        }
    return {
      "status":"BLOCKED_INSUFFICIENT_OR_MIXED_RELATIONS",
      "unclassified":True,"render_allowed":False,
    }

def audit_verified_source(doc,html_text,*,source_sha256=None,proof_from_https=False):
    """Offline tests may call this but are *NEVER* recorded as live verified."""
    SOURCE.validate_document(doc)
    spans=_excerpt_spans(doc,html_text)
    graph=extract(spans)
    if proof_from_https:
        if not isinstance(source_sha256,str) or not re.fullmatch("[0-9a-f]{64}",source_sha256):
            fail("SHA_AUSENTE")
    # Source verifies the excerpt, not machine geometry or visual similarity.
    return {
        "schema":SCHEMA,
        "source_id":doc["id"],"source_url":doc["url"],
        "source_live_verified":bool(proof_from_https),
        "source_sha256":source_sha256 if proof_from_https else None,
        "source_excerpt_count":len(spans),
        "graph":graph,
        "capability_gap":_topology_gaps(graph),
        "source_text_not_full_document_preserved":True,
        "all_claims_have_span_id":all(e["supported_span_ids"] for e in graph["edges"]),
        "source_does_not_establish_kinematic_dimensions":True,
        "input_output_designation_verified":False,
        "visual_reference_rights_verified":False,
        "third_party_media_copied":False,
        "full_f15_compile_allowed":False,
        "render_allowed":False,"publication_allowed":False,
        "human_review_required":True,
    }

def run(doc_path,output_dir,*,live=False):
    doc=SOURCE.load_document(doc_path)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    record={
       "schema":SCHEMA,"source_id":doc["id"],"source_url":doc["url"],
       "source_live_verified":False,
       "status":"BLOCKED_NO_LIVE_SOURCE",
       "render_allowed":False,"publication_allowed":False,
       "human_review_required":True,
       "visual_reference_rights_verified":False,
    }
    if live:
        try:
            download=SOURCE.fetch_html(doc["url"])
            if download["final_url"]!=doc["url"]:
                fail("FINAL_URL_DIFFERS")
            record=audit_verified_source(doc,download["text"],
                 source_sha256=download["raw_sha256"],proof_from_https=True)
            record["status"]=record["capability_gap"]["status"]
            record["source_mime"]=download["mime"]
        except (ValueError,OSError) as exc:
            # Unverifiable source, anchors, or outage MUST NOT become a graph.
            record["status"]="BLOCKED_SOURCE_"+type(exc).__name__
            record["source_error"]=str(exc)[:180]
    out_file=out/(doc["id"]+"_F17_RELATIONS.json")
    out_file.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf8")
    return record

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    result=run(args.manifest,args.output,live=args.live)
    print(json.dumps({"source":result["source_id"],"live":result["source_live_verified"],
       "status":result["status"],"render":False,"published":False},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
