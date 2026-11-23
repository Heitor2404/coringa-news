"""E6 tests: typed evidence classes are NEVER automatically E1 joint instances."""
import copy
import hashlib
import json

import pytest

from src.v4.formatos import extracao_juntas_e6 as E6

@pytest.mark.parametrize(("sentence","expected"),[
    ("The rotating drive wheel is equipped with a pin that reaches into a slot located in another wheel.",
     "pin_in_slot"),
    ("The drive pin enters and leaves the slot during the cycle.",
     "pin_in_slot"),
    ("A yoke slot engages a pin on another wheel.","pin_in_slot"),
    ("The sliding piston in a cylinder drives the rotating crank.","sliding_in_guide"),
    ("The piston slides along the guide and continues moving.","sliding_in_guide"),
    ("A circular gear, the pinion, engaging a linear gear, the rack, transfers rotation.",
     "rack_engages_pinion"),
    ("The pinion engages a rack placed next to the rail.","rack_engages_pinion"),
])
def test_specific_relation_text_detected_but_not_safe_for_solver(sentence,expected):
    r=E6.typed(sentence,sentence_id="s1")
    assert r["relation_type"]==expected
    assert r["solver_joint_kind_candidate"] in ("slot","slider","rack_pinion")
    assert r["status"]=="TYPED_TEXT_CANDIDATE_UNREVIEWED"
    assert r["evidence_sentence_sha256"]==hashlib.sha256(sentence.encode()).hexdigest()
    assert r["body_instances_bound"] is False
    assert r["joint_anchor_coordinates_verified"] is False
    assert r["source_dimensions_bound_to_joint"] is False
    assert not r["safe_for_solver"] and not r["render_allowed"] and not r["publish"]

@pytest.mark.parametrize("sentence",[
    "They were connected to the driving rods that powered the wheel.",
    "It engages the slot attached to the wheel.",
    "This pinion engages a linear rack.",
    "The pinion does not engage the rack.",
    "A pin could enter the slot if its shaft moved.",
    "A pin and slot might be connected by a yoke.",
    "The Geneva drive has four slots and a crank pin, but this isn't a full drawing.",
    "The slider crank has three revolute joints and one prismatic joint.",
    "The follower arm connects the crank arm to the slider.",
    "A cam follower is designed to follow cam lobe profiles.",
    "The pinion is connected to a lever and displaces a vertical rack.",
    "The circular gear pinion can simultaneously drive two racks.",
    "A pair of hinges is connected by a cross shaft.",
    "Does the rack engage the pinion?",
])
def test_ambiguous_bodies_negation_hypotheticals_and_untyped_edges_abstain(sentence):
    result=E6.typed(sentence,sentence_id="s2")
    assert result["status"]=="ABSTAIN",(sentence,result)
    assert result["relation_type"] is None
    assert result["solver_joint_kind_candidate"] is None
    assert result["safe_for_solver"] is False

def test_numeric_example_is_converted_but_never_used_as_design_parameters():
    sentence='For example, for rod length 6" and crank radius 2", solving the formula gives a speed.'
    found=E6.measurements(sentence,sentence_id="s18")
    assert len(found)==2,found
    values={(x["part_word"],x["dimension_word"]):x["value_in_m"] for x in found}
    assert values[("rod","length")]==pytest.approx(.1524)
    assert values[("crank","radius")]==pytest.approx(.0508)
    assert all(not x["specific_machine_identity_verified"] for x in found)
    assert all(not x["part_instance_verified"] and not x["safe_to_fill_spec"] for x in found)
    assert E6.measurements("The drive has 20 teeth and rotates by 90 degrees.",sentence_id="s1")==[]

def test_explicit_wrong_joint_class_counts_as_false_positive_and_false_negative():
    expected=["pin_in_slot","sliding_in_guide",None,None]
    actual=["rack_engages_pinion","sliding_in_guide",None,"pin_in_slot"]
    r=E6.score(expected,actual)
    assert (r["tp"],r["fp"],r["fn"],r["tn"])==(1,2,1,1)
    assert r["precision"]==pytest.approx(1/3)
    assert r["recall"]==pytest.approx(0.5)

def test_no_positive_predictions_returns_no_invented_precision():
    r=E6.score([None,None], [None,None])
    assert r["precision"] is None and r["recall"] is None
    assert r["tn"]==2
    with pytest.raises(ValueError,match="E6-PROVA-CONTAGEM"):
        E6.score([None],[])

def test_no_unbacked_gold_version_or_duplicate_source_ids():
    gold={"schema":E6.GOLD_SCHEMA,"gold_frozen":True,
          "allow_label_changes_for_metric":False,
          "pages":[{"pageid":1}]*5}
    with pytest.raises(ValueError,match="E6-PROVA-DUPLICADO"):
        E6.evaluate(gold,fetch=lambda _:None)
    gold["gold_frozen"]=False
    with pytest.raises(ValueError,match="E6-PROVA-CONTRATO_GOLD"):
        E6.evaluate(gold,fetch=lambda _:None)

def test_revision_drift_is_blocking_not_silent_relabeling():
    gold={"schema":E6.GOLD_SCHEMA,"gold_frozen":True,
          "allow_label_changes_for_metric":False,
          "pages":[{"title":"Article","pageid":i,"revid":5,
                    "text_sha256":"a"*64,"count":2,"split":"development",
                    "positive_types":{}} for i in range(1,6)]}
    def fake(_):
        return {"pageid":1,"revid":6,"text_sha256":"b"*64}
    with pytest.raises(ValueError,match="E6-PROVA-SOURCE_REVISION_DRIFT"):
        E6.evaluate(gold,fetch=fake)

def test_typing_result_has_no_auto_image_or_publication_path():
    for sentence in ("The pin engages the slot.",
                     "The pinion meshes with a rack.",
                     "A piston slides in the cylinder."):
        result=E6.typed(sentence,sentence_id="w2")
        for name in ("solvable_mechanism_spec","safe_for_solver",
                     "render_allowed","publish"):
            assert result[name] is False
        assert result["human_review_required"] is True

def test_invalid_ids_or_overlong_source_are_rejected():
    with pytest.raises(ValueError,match="E6-PROVA-ENTRADA"):
        E6.typed("x"*301,sentence_id="s1")
    with pytest.raises(ValueError,match="E6-PROVA-ENTRADA"):
        E6.typed("The pin engages the slot.",sentence_id="x/../../safe")
    with pytest.raises(ValueError,match="E6-PROVA-ENTRADA"):
        E6.measurements("A rod length 3 mm.",sentence_id="1")
