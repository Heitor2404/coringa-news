"""Offline E5 adversarial tests: no simulated fixture counted as live source."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.v4.formatos import extrator_relacoes_e5 as E5
from src.v4.formatos import relacoes_com_evidencia_f17 as F17

@pytest.mark.parametrize("sentence",(
    "A connecting rod connects the piston to the crankshaft.",
    "The small end attaches to the gudgeon pin and the piston.",
    "The slot engages the pin on the rotating part.",
    "A hinge between the piston and connecting rod is located outside the cylinder.",
    "The master rod has a direct attachment to the crankshaft and piston.",
    "Articulated connecting rods comprise a master rod attached to a crank pin.",
))
def test_explicit_named_connection_is_candidate_only(sentence):
    r=E5.candidate(sentence,sentence_id="s1")
    assert r["candidate"] is True
    assert len(r["candidate_component_mentions"])>=2
    assert r["matched_evidence_id"]=="s1"
    assert r["relation_kind"]=="unspecified_physical_connection"
    assert r["joint_kind_verified"] is False
    assert r["body_instances_bound"] is False
    assert r["measurements_verified"] is False
    assert not r["safe_for_solver"] and not r["render_allowed"]

@pytest.mark.parametrize("sentence",(
    "A connecting rod and crankshaft are listed in the parts catalog.",
    "A connecting rod rotates while the piston moves down.",
    "The crank pin is connected to no connecting rod.",
    "The connecting rod does not connect the piston to the crankshaft.",
    "The crankpin is used instead of the connecting rod.",
    "A link connecting to ground by a revolute joint is called a crank link.",
    "A coupler connecting a crank and slider is often called a connecting rod.",
    "In general, each joint connects two links in a mechanism.",
    "The master rod and the slave rod might connect to the crank pin.",
    "Does the connecting rod connect to the crankshaft?",
    "They were connected to the driving rods that transmitted power.",
    "The connecting rod has a crank pin and a piston at opposite ends.",
    "The six-bar linkage has two ternary links not connected to each other.",
))
def test_nonclaims_negations_generic_and_ambiguous_pronouns_are_rejected(sentence):
    result=E5.candidate(sentence,sentence_id="s2")
    assert result["candidate"] is False, (sentence,result)
    assert result["matched_evidence_id"] is None
    assert result["candidate_component_mentions"]==[]

def test_noun_connecting_rod_and_pin_are_not_predicates():
    a=E5.candidate("The connecting rod has a crank pin and a piston.",sentence_id="s8")
    assert not a["candidate"]
    assert "NO_EXPLICIT_LINK_VERB" in a["suppression_reasons"]
    b=E5.candidate("The piston pins their connecting rods to the master rod.",sentence_id="s9")
    assert b["candidate"]

def test_f17_and_e5_are_not_the_same_level_of_assertion():
    s="The crankpin connects to the larger end of the connecting rod."
    baseline=F17.extract([{"id":"w7","text":s,"supported":True}])
    r=E5.candidate(s,sentence_id="w7")
    assert baseline["edges"]==[]
    assert r["candidate"] and r["joint_kind_verified"] is False

def test_source_selection_is_deterministic_and_preserves_text_hashes():
    s=("The slot engages a pin on the rotating part. "
       "A four-bar mechanism is connected in a loop by four joints. "
       "A connecting rod connects the piston to a crankshaft. "
       "This sentence contains only background facts about a time period.")
    rows=E5.selected_e5(s)
    assert len(rows)>=2
    for i,x in enumerate(rows):
        assert x["sentence_id"]=="s"+str(i+1)
        assert x["text_sha256"]==hashlib.sha256(x["text"].encode()).hexdigest()

def test_golden_revision_fingerprint_mismatch_is_a_hard_block():
    fake={
       "schema":E5.GOLD_SCHEMA,"benchmark_freeze":True,
       "pages":[{"pageid":i,"title":"Mechanism","revid":100,
                 "text_sha256":"a"*64,"selection":"e5","count":1,
                 "split":"heldout" if i==4 else "development",
                 "positive_sentence_ids":[]} for i in range(1,5)]}
    def injected(_):return {"pageid":1,"revid":999,"text_sha256":"b"*64}
    with pytest.raises(ValueError,match="E5-AVALIACAO-SOURCE_REVISION_DRIFT"):
        E5.evaluate_gold(fake,fetch=injected)

def test_gold_cannot_duplicate_pageid_or_use_unknown_split():
    fake={
       "schema":E5.GOLD_SCHEMA,"benchmark_freeze":True,
       "pages":[{"pageid":1,"title":"Mechanism","revid":100,
                 "text_sha256":"a"*64,"selection":"e5","count":1,
                 "split":"development","positive_sentence_ids":[]} for _ in range(4)]}
    with pytest.raises(ValueError,match="E5-AVALIACAO-DUPLICADO"):
        E5.evaluate_gold(fake,fetch=lambda _:None)

def test_metrics_display_undefined_precision_without_inventing_accuracy():
    z=E5._metrics([False,False],[False,False])
    assert z["precision"] is None and z["recall"] is None
    assert z["tn"]==2
    m=E5._metrics([True,False,True],[True,True,False])
    assert (m["tp"],m["fn"],m["fp"],m["tn"])==(1,1,1,0)
    assert m["precision"]==0.5 and m["recall"]==0.5
