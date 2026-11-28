"""E6: conservative typed-contact evidence from revision-pinned public text.

No LLM, no name/title-based routing, no claim that a lexeme determines mounting
geometry. Relation classes are LABELS for review, not joint instances: E1/E2
solver input remains blocked until there are body IDs and sourced dimensions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from src.v4.formatos import descoberta_fontes_e4 as E4
from src.v4.formatos import extrator_relacoes_e5 as E5

SCHEMA="coringa-e6-typed-relation-audit-v1"
GOLD_SCHEMA="coringa-e6-joint-evidence-gold-v1"
CATEGORIES={"pin_in_slot":"slot","sliding_in_guide":"slider",
            "rack_engages_pinion":"rack_pinion"}
ANAPHORA=re.compile(
    r"^\s*(?:(?:and|but|however|conversely|also|together|therefore)\s*,?\s*)?"
    r"(?:they|them|their|it|its|these|those|he|she|this|such|both|which)"
    r"\b",re.I)
NEG=re.compile(r"\b(?:no|not|never|cannot|without|rather than|instead of)\b",re.I)
HYPOTHETICAL=re.compile(
    r"\b(?:might|may|would|could|hypothetically|perhaps|imaginary)\b",re.I)
PIN_SLOT=re.compile(
    r"\b(?:pin|pins|crankpin|drive pin)\b"
    r"(?:(?![.!?]).){0,115}?"
    r"\b(?:reaches?\s+into|enters?|entering|engages?|"
    r"moves?\s+(?:in|inside)|fits?\s+(?:in|inside))\b"
    r"(?:(?![.!?]).){0,75}?\bslots?\b"
    r"|\bslots?\b(?:(?![.!?]).){0,65}?"
    r"\b(?:engages?|receives?|contains?)\b"
    r"(?:(?![.!?]).){0,65}?\bpins?\b",re.I)
RACK_PINION=re.compile(r"\b(?:rack|racks)\b",re.I)
PINION=re.compile(r"\b(?:pinion|pinions)\b",re.I)
ENGAGEMENT=re.compile(r"\b(?:engages?|engaging|engaged|meshes?|meshing)\b",re.I)
SLIDE=re.compile(
    r"\b(?:sliding|slides?|slid)\s+"
    r"(?:[a-z-]+\s+){0,3}?"
    r"(?:pistons?|sliders?|rods?|blocks?)\s+"
    r"(?:in|inside|along|within|through)\s+(?:an?\s+|the\s+)?"
    r"(?:cylinder|bore|guide|track|rail|channel)\b"
    r"|\b(?:pistons?|sliders?|rods?|blocks?)\s+"
    r"(?:slides?|slid)\s+(?:in|inside|along|within|through)\s+"
    r"(?:an?\s+|the\s+)?(?:cylinder|bore|guide|track|rail|channel)\b",re.I)
SLOT_OWNER=re.compile(r"\b(?:slot|groove|guideway)\b",re.I)
PARTS=r"(?:connecting\s+rod|rod|crank|shaft|piston|wheel|pinion|rack|link|arm)"
LINEAR=re.compile(
    rf"\b(?P<part>{PARTS})\s+(?P<dimension>length|radius|diameter|stroke)"
    rf"\s+(?:of\s+)?(?P<number>\d+(?:\.\d+)?)\s*"
    rf"(?P<unit>millimetres?|millimeters?|centimetres?|centimeters?|"
    rf"inches?|inch|mm|cm|m|metres?|meters?|\"|\u2033)(?=$|[\s,.;)\]])",re.I)
# Dedicated units parser avoids accidental geometry from "20 teeth" or 90 degrees.
UNIT_TO_M={
 "mm":.001,"millimetre":.001,"millimetres":.001,
 "millimeter":.001,"millimeters":.001,
 "cm":.01,"centimetre":.01,"centimetres":.01,
 "centimeter":.01,"centimeters":.01,
 "m":1.,"metre":1.,"metres":1.,"meter":1.,"meters":1.,
 "inch":.0254,"inches":.0254,'"':.0254,"\u2033":.0254,
}
SENT_ID=re.compile(r"^[sw]\d{1,3}$")

def fail(code):
    raise ValueError("E6-PROVA-"+code)

def typed(sentence,*,sentence_id):
    """Return one narrow evidence candidate, or abstain explicitly.

    Only words in the provided sentence count. No cross-sentence inference.
    The same sentence can mention many parts yet lack a trustworthy joint.
    """
    if (not isinstance(sentence,str) or len(sentence)>300 or not
        isinstance(sentence_id,str) or not SENT_ID.fullmatch(sentence_id)):
        fail("ENTRADA")
    reasons=[]
    if ANAPHORA.search(sentence):
        reasons.append("UNRESOLVED_SUBJECT_OR_ANTECEDENT")
    if NEG.search(sentence):
        reasons.append("NEGATED_OR_ALTERNATIVE")
    if HYPOTHETICAL.search(sentence) or "?" in sentence:
        reasons.append("NON_ASSERTIVE")
    if re.match(r"\s*={1,5}",sentence):
        reasons.append("HEADING")
    detected=[]
    if PIN_SLOT.search(sentence):
        detected.append("pin_in_slot")
    if RACK_PINION.search(sentence) and PINION.search(sentence) and ENGAGEMENT.search(sentence):
        detected.append("rack_engages_pinion")
    if SLIDE.search(sentence):
        detected.append("sliding_in_guide")
    if len(detected)>1:
        reasons.append("MULTIPLE_RELATION_TYPES_REQUIRE_DISAMBIGUATION")
    if not detected:
        reasons.append("NO_NARROW_EXPLICIT_RELATION")
    chosen=detected[0] if len(detected)==1 and not reasons else None
    feature_words={
        "pin_in_slot":["pin","slot"],
        "rack_engages_pinion":["pinion","rack"],
        "sliding_in_guide":["slider_or_piston","guide_or_cylinder"],
    }
    return {
        "sentence_id":sentence_id,
        "status":"TYPED_TEXT_CANDIDATE_UNREVIEWED" if chosen else "ABSTAIN",
        "relation_type":chosen,
        "solver_joint_kind_candidate":CATEGORIES[chosen] if chosen else None,
        "relation_features":feature_words[chosen] if chosen else [],
        "evidence_sentence_sha256":hashlib.sha256(sentence.encode("utf8")).hexdigest()
            if chosen else None,
        "rejection_reasons":reasons,
        "body_instances_bound":False,
        "joint_anchor_coordinates_verified":False,
        "source_dimensions_bound_to_joint":False,
        "solvable_mechanism_spec":False,
        "safe_for_solver":False,
        "human_review_required":True,
        "render_allowed":False,"publish":False,
    }

def measurements(sentence,*,sentence_id):
    """Extract an explicit length/radius and convert units, not engineering data.

    A numeric example in Wikipedia is not a real machine specification. Even a
    typed number with units is NOT allowed to populate MechanismSpec.
    """
    if (not isinstance(sentence,str) or len(sentence)>300 or not
        isinstance(sentence_id,str) or not SENT_ID.fullmatch(sentence_id)):
        fail("ENTRADA")
    out=[]
    for match in LINEAR.finditer(sentence):
        unit=match.group("unit").casefold()
        if unit not in UNIT_TO_M:continue
        value=float(match.group("number"))
        if not 0<value<100000:continue
        out.append({
            "sentence_id":sentence_id,
            "verbatim":match.group(0),
            "part_word":match.group("part").casefold(),
            "dimension_word":match.group("dimension").casefold(),
            "source_value":value,"source_unit":unit,
            "value_in_m":value*UNIT_TO_M[unit],
            "source_sentence_sha256":hashlib.sha256(sentence.encode("utf8")).hexdigest(),
            "context":"EXAMPLE_OR_UNVERIFIED_MACHINE_VARIANT",
            "specific_machine_identity_verified":False,
            "part_instance_verified":False,
            "safe_to_fill_spec":False,
            "human_review_required":True,
        })
    return out

def score(expected,predicted):
    """Type-specific exact match; a wrong class counts as FP + FN."""
    if len(expected)!=len(predicted):fail("CONTAGEM")
    tp=fp=fn=tn=0
    for truth,pred in zip(expected,predicted):
        if truth==pred and truth is not None:tp+=1
        elif truth is None and pred is None:tn+=1
        else:
            if truth is not None:fn+=1
            if pred is not None:fp+=1
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,
            "positive_support":tp+fn,"negative_support":tn+
                sum(a is None and b is not None
                    for a,b in zip(expected,predicted)),
            "samples":len(expected)}

def evaluate(gold,*,fetch=E4.fetch_page):
    if (not isinstance(gold,dict) or gold.get("schema")!=GOLD_SCHEMA or
        gold.get("gold_frozen") is not True or
        gold.get("allow_label_changes_for_metric") is not False):
        fail("CONTRATO_GOLD")
    pages=gold.get("pages")
    if not isinstance(pages,list) or len(pages)!=5:fail("PAGINAS_GOLD")
    if len({p["pageid"] for p in pages})!=len(pages):fail("DUPLICADO")
    splits={"development":{"y":[],"p":[]},"heldout":{"y":[],"p":[]}}
    records=[]
    for spec in pages:
        if set(spec)!={"title","pageid","revid","text_sha256","count",
                       "split","positive_types"}:fail("CONTRATO_PAGINA")
        if spec["split"] not in splits or spec["count"]<1:fail("DIVISAO")
        raw=fetch({"pageid":spec["pageid"],"title":spec["title"]})
        if any(raw.get(field)!=spec[field] for field in
               ("pageid","revid","text_sha256")):
            fail("SOURCE_REVISION_DRIFT")
        rows=E5.selected_e5(raw["plain_text"])
        if len(rows)!=spec["count"]:fail("SELECAO_DIVERGIU")
        ids={r["sentence_id"] for r in rows}
        if (len(ids)!=len(rows) or not isinstance(spec["positive_types"],dict) or
            set(spec["positive_types"])-ids or
            set(spec["positive_types"].values())-set(CATEGORIES)):
            fail("ROTULOS_INVALIDOS")
        split=splits[spec["split"]]
        candidates=[];numbers=[];errors=[]
        for row in rows:
            label=spec["positive_types"].get(row["sentence_id"])
            e=typed(row["text"],sentence_id=row["sentence_id"])
            prediction=e["relation_type"]
            split["y"].append(label);split["p"].append(prediction)
            if prediction:
                candidates.append({
                    "sentence_id":row["sentence_id"],
                    "sentence_sha256":e["evidence_sentence_sha256"],
                    "relation_type":prediction,
                    "solver_joint_kind_candidate":e["solver_joint_kind_candidate"],
                    "source_pageid":raw["pageid"],"source_revid":raw["revid"],
                    "source_text_sha256":raw["text_sha256"],
                    "body_instances_bound":False,"safe_for_solver":False,
                })
            if prediction!=label:
                errors.append({"sentence_id":row["sentence_id"],
                               "expected":label,"predicted":prediction,
                               "rejection_reasons":e["rejection_reasons"]})
            numbers.extend(measurements(row["text"],sentence_id=row["sentence_id"]))
        records.append({
            "title":spec["title"],"pageid":raw["pageid"],
            "revid":raw["revid"],"source_url":raw["source_url"],
            "source_text_sha256":raw["text_sha256"],"split":spec["split"],
            "sentences":len(rows),"gold_types":spec["positive_types"],
            "candidates":candidates,"measurements_not_usable":numbers,
            "misclassifications":errors,
            "all_sources_are_revision_checked":True,
        })
    metrics={label:score(items["y"],items["p"])
             for label,items in splits.items()}
    return {
        "schema":SCHEMA,"status":"TYPED_TEXT_CANDIDATES_ONLY",
        "transport":"MEDIAWIKI_FETCH_BY_PAGEID_REVISION_CHECK",
        "source_pages_refetched":len(records),
        "source_revisions_verified":True,
        "target_is_typed_text_not_solver_joint":True,
        "labels_reviewed_independently":False,
        "manual_gold_labels_frozen":True,
        "metrics":metrics,"pages":records,
        "source_to_mechanism_spec":False,
        "joint_instance_endpoints_verified":0,
        "dimension_fields_bound_to_instances":0,
        "new_mechanism_simulations":0,
        "cost_paid_llm_usd":0,
        "human_review_required":True,"render_allowed":False,"publish":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("gold",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    report=evaluate(json.loads(args.gold.read_text("utf8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"status":report["status"],"metrics":report["metrics"],
                      "source_pages":report["source_pages_refetched"],
                      "automatic_specs":0,"publish":False},ensure_ascii=False))
if __name__=="__main__":
    main()
