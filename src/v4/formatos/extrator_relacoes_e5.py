"""E5 experimental sentence-level connection detector + revision-locked audit.

Conservative, no LLM. Recognizes explicit lexical attachment/engagement/pinning
between named mechanical component mentions, NOT an E1 joint or its endpoints.
No publishing, geometry generation, force claims or image reuse. NEVER interpret
a retrieval snippet, a general mechanism definition, or a negative sentence as
a physical joint. Gold labels are frozen separately by Wikipedia page revision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from src.v4.formatos import descoberta_fontes_e4 as SOURCE
from src.v4.formatos import relacoes_com_evidencia_f17 as F17

SCHEMA="coringa-e5-connection-candidates-v1"
GOLD_SCHEMA="coringa-e5-explicit-connection-gold-v1"
VOCAB=("connect","attach","pin","joint","hinge","engag","slot",
       "piston","crank","coupl","slide","sliding","rotat",
       "bearing","gear","shaft","rod","engine")
# Shared component lexicon, not mechanism-title routing or a complete ontology.
# Mention detection is NOT instance identity or proof of a particular joint.
COMPONENTS=(
    "connecting rods?", "crankshafts?", "crank ?pins?", "crankpins?",
    "gudgeon pins?", "wrist pins?", "piston rods?", "pistons?",
    "crossheads?", "small ends?", "big ends?", "larger ends?",
    "master rods?", "slave rods?", "rods?", "cranks?", "yokes?",
    "slots?", "pins?", "sliding blocks?", "rotating parts?",
    "discs?", "arms?", "shafts?", "flywheels?", "rockers?",
    "gears?", "wheels?", "bearings?", "ground",
)
# 'connect', 'attach', 'couple' etc express *candidate* relations.
# 'pin' is included only as a verb with pronoun/number context, not a noun.
REL_VERB=re.compile(r"\b(?:connects?|connected|attaches?|attached|"
                    r"attachments?|engages?|engaged|couples?|coupled|"
                    r"hinges?|hinged|pinned|pinning)\b"
                    r"|\b(?:pin|pins)\s+(?:their|its|the)\b"
                    r"|\bconnecting\s+(?:to|with|a|an|the)\b",re.I)
COMP_RE=re.compile(r"\b(?:"+"|".join(COMPONENTS)+r")\b",re.I)
NEG=re.compile(r"\b(?:not|never|without|cannot|does not|no|instead of|rather than)\b",re.I)
GENERIC=re.compile(r"^\s*(?:a link\b|a coupler\b|a joint\b|each joint\b|"
                   r"in general\b|generally\b|a generic\b)",re.I)
HEADING=re.compile(r"^\s*={1,5}")

def fail(code):raise ValueError("E5-AVALIACAO-"+code)

def selected_e5(text):
    """Exact selection used in the E5 live collection action, no LLM and no title branching."""
    if not isinstance(text,str):fail("TEXTO")
    sentences=re.split(r"(?<=[.!?])\s+|\s*\n+\s*",text)
    selected=[]
    for raw in sentences:
        sentence=" ".join(raw.split())
        if 34<=len(sentence)<=260 and any(x in sentence.casefold() for x in VOCAB):
            selected.append({"sentence_id":"s"+str(len(selected)+1),"text":sentence,
                             "text_sha256":hashlib.sha256(sentence.encode()).hexdigest()})
        if len(selected)>=40:break
    return selected

def mentions(sentence):
    """Nonoverlapping terms, without claiming body instances or mounting positions."""
    found=[];ends=[]
    for m in COMP_RE.finditer(sentence):
        if any(m.start()<e and m.end()>b for b,e in ends):continue
        found.append(m.group(0).lower())
        ends.append((m.start(),m.end()))
    return found

def candidate(sentence,*,sentence_id):
    if not isinstance(sentence,str) or not isinstance(sentence_id,str) or not re.fullmatch(r"[sw]\d{1,3}",sentence_id):
        fail("ENTRADA")
    names=mentions(sentence)
    pred=REL_VERB.search(sentence)
    excluded=[]
    if HEADING.search(sentence):excluded.append("HEADER")
    if NEG.search(sentence):excluded.append("NEGATIVE_OR_ALTERNATIVE")
    if GENERIC.search(sentence):excluded.append("GENERIC_DEFINITION")
    if len(names)<2:excluded.append("INSUFFICIENT_NAMED_COMPONENTS")
    if not pred:excluded.append("NO_EXPLICIT_LINK_VERB")
    return {
        "sentence_id":sentence_id,
        "candidate":bool(not excluded),
        "candidate_component_mentions":names if not excluded else [],
        "matched_predicate":pred.group(0) if pred and not excluded else None,
        "matched_evidence_id":sentence_id if not excluded else None,
        "relation_kind":"unspecified_physical_connection" if not excluded else None,
        "suppression_reasons":excluded,
        "body_instances_bound":False,"joint_kind_verified":False,
        "joint_axes_verified":False,"measurements_verified":False,
        "human_review_required":True,"safe_for_solver":False,"render_allowed":False,
    }

def _metrics(predicted,expected):
    tp=sum(x and y for x,y in zip(predicted,expected))
    fp=sum(x and not y for x,y in zip(predicted,expected))
    fn=sum(not x and y for x,y in zip(predicted,expected))
    tn=sum(not x and not y for x,y in zip(predicted,expected))
    precision=(tp/(tp+fp)) if tp+fp else None
    recall=(tp/(tp+fn)) if tp+fn else None
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":precision,"recall":recall,
            "support_positive":tp+fn,"support_negative":tn+fp}

def evaluate_gold(gold,*,fetch=SOURCE.fetch_page):
    """Re-fetch source text, confirm frozen page revision AND SHA or refuse.
    A monkeypatched fetch in tests is only a fixture and not external proof.
    Only CI's genuine default transport is counted as public source retrieval.
    """
    if (not isinstance(gold,dict) or gold.get("schema")!=GOLD_SCHEMA
        or gold.get("benchmark_freeze") is not True):fail("GOLD")
    pages=gold.get("pages")
    if not isinstance(pages,list) or not 4<=len(pages)<=12:fail("PAGINAS")
    if len({p["pageid"] for p in pages})!=len(pages):fail("DUPLICADO")
    groups={"development":{"baseline":[],"e5":[],"gold":[]},
            "heldout":{"baseline":[],"e5":[],"gold":[]}}
    summaries=[]
    for record in pages:
        if set(record)!={"pageid","title","revid","text_sha256","selection",
                         "count","split","positive_sentence_ids"}:fail("CONTRATO_PAGINA")
        if record["split"] not in groups or record["selection"] not in ("e4","e5"):
            fail("CONTRATO_PAGINA")
        # The request title is a locator only; identity & revision are checked below.
        actual=fetch({"pageid":record["pageid"],"title":record["title"]})
        if (actual["pageid"]!=record["pageid"]
            or actual["revid"]!=record["revid"]
            or actual["text_sha256"]!=record["text_sha256"]):
            fail("SOURCE_REVISION_DRIFT")
        if record["selection"]=="e4":
            spans=SOURCE.derive_evidence(actual)["evidence_spans"]
            selected=[{"sentence_id":s["id"],"text":s["text"]} for s in spans]
        else:selected=selected_e5(actual["plain_text"])
        if len(selected)!=record["count"]:fail("SENTENCE_SELECTION_DRIFT")
        ids={s["sentence_id"] for s in selected}
        if len(ids)!=len(selected) or set(record["positive_sentence_ids"])-ids:
            fail("GOLD_LABEL_MISMATCH")
        group=groups[record["split"]]
        candidates=[]
        for row in selected:
            sid=row["sentence_id"]
            y=sid in record["positive_sentence_ids"]
            # Same binary benchmark target, F17 baseline is typed-joint only:
            # "does this sentence produce ANY explicitly sourced F17 edge?"
            baseline=bool(F17.extract([{"id":sid,"text":row["text"],
                                        "supported":True}])["edges"])
            found=candidate(row["text"],sentence_id=sid)
            group["gold"].append(y);group["baseline"].append(baseline)
            group["e5"].append(found["candidate"])
            if found["candidate"]:
                candidates.append({"sentence_id":sid,
                    "source_sha256":actual["text_sha256"],
                    "sentence_sha256":hashlib.sha256(row["text"].encode()).hexdigest(),
                    "predicate":found["matched_predicate"],
                    "components":found["candidate_component_mentions"],
                    "relation_kind":found["relation_kind"],
                    "requires_human_review":True,
                    "body_instances_bound":False,"safe_for_solver":False})
        summaries.append({
            "pageid":record["pageid"],"revid":record["revid"],
            "source_url":actual["source_url"],"text_sha256":actual["text_sha256"],
            "split":record["split"],"sentences":len(selected),
            "gold_positive":len(record["positive_sentence_ids"]),
            "e5_candidates":len(candidates),
            "candidates":candidates,
            "source_revision_confirmed":True,
            "source_text_from_search_snippet":False,
        })
    metric={}
    for name,group in groups.items():
        metric[name]={"baseline":_metrics(group["baseline"],group["gold"]),
                      "e5":_metrics(group["e5"],group["gold"])}
    return {
        "schema":SCHEMA,
        "status":"TEXT_RELATION_EVALUATION_ONLY",
        "evaluation_compares_binary_connection_evidence_not_typed_joint_accuracy":True,
        "manual_gold_labels_no_independent_review":True,
        "source_pages_live_refetched":len(pages),
        "source_revisions_verified":True,
        "source_selection_reproduced":True,
        "gold_is_frozen":True,
        "split_by_source_page":True,
        "metrics":metric,
        "pages":summaries,
        "joint_endpoints_validated":0,
        "geometry_bound_from_source":0,
        "autonomous_specs_generated":0,
        "holdout_mechanism_simulations":0,
        "paid_llm_calls":0,
        "human_review_required":True,"publish":False,"render_allowed":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("gold",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    gold=json.loads(args.gold.read_text("utf8"))
    report=evaluate_gold(gold)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"status":report["status"],"metrics":report["metrics"],
                       "source_pages_verified":report["source_pages_live_refetched"],
                       "auto_specs":0,"publish":False},ensure_ascii=False))
if __name__=="__main__":main()
