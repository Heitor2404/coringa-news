"""E4 discovery tests are mocked and NEVER count as external API proof."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.v4.formatos import descoberta_fontes_e4 as E4

TEXT=(
    "The crank is hinged to the connecting rod. "
    "The connecting rod is hinged to the piston. "
    "The piston slides inside the cylinder along a straight line. "
    "The crank length is 20 mm in this illustrative example. "
    "The example was published in 2012. "
    "These components can reciprocate under a crank drive."
)

class FakeAPI:
    def __init__(self, *, mode="ok"):
        self.requests=[]
        self.mode=mode
    def __call__(self,params):
        self.requests.append(copy.deepcopy(params))
        if params.get("list")=="search":
            return {"query":{"search":[
                {"ns":0,"pageid":91,"title":"Slider-crank linkage",
                 "snippet":"The crank length is 99 mm in a fake search snippet."},
                {"ns":0,"pageid":92,"title":"Totally different article",
                 "snippet":"Not engineering evidence."},
                {"ns":1,"pageid":93,"title":"Talk:Slider-crank linkage"}
            ]}}
        p=int(params["pageids"])
        if p==91:
            return {"query":{"pages":[{
                "pageid":91,"title":"Slider-crank linkage","extract":TEXT,
                "revisions":[{"revid":1981,"parentid":1980}]
            }]}}
        if self.mode=="badid":
            return {"query":{"pages":[{
                "pageid":999,"title":"Wrong article","extract":TEXT,
                "revisions":[{"revid":345}]
            }]}}
        return {"query":{"pages":[{
            "pageid":92,"title":"Totally different article",
            "extract":"This page has no mechanical content and is merely a long text passage "
                      "for testing retrieval from a second search result.",
            "revisions":[{"revid":1990}]
        }]}}


def test_live_discovery_never_accepts_mocked_network(tmp_path):
    with pytest.raises(ValueError,match="E4-FONTE-MOCK_NAO_E_FONTE_LIVE"):
        E4.discover("slider crank linkage",tmp_path,get_json=FakeAPI(),
                    real_network=True)


def test_mocked_search_fetches_by_pageid_not_search_snippet(tmp_path):
    fake=FakeAPI()
    r=E4.discover("slider crank linkage",tmp_path,get_json=fake)
    assert r["status"]=="MOCKED_DISCOVERY_NO_LIVE_CLAIM"
    assert r["URLs_pre_registered"] is False
    assert r["query_human_supplied"] is True
    assert r["real_network_verified"] is False
    assert r["mechanism_spec_generated"] is False
    assert len(r["pages"])==2
    assert all(not x["source_live_verified"] for x in r["pages"])
    assert 99 not in [q["number"] for q in r["pages"][0]["candidate_quantities"]]
    assert r["pages"][0]["pageid"]==91 and r["pages"][0]["revid"]==1981
    assert r["pages"][0]["source_url"].endswith("/Slider-crank_linkage")
    assert r["pages"][0]["text_sha256"]==hashlib.sha256(TEXT.encode()).hexdigest()
    assert fake.requests[0]["list"]=="search"
    assert all("pageids" in v for v in fake.requests[1:])
    assert not r["publish"] and not r["render_allowed"]


def test_extracted_spans_have_exact_source_text_and_cross_module_relations():
    fake=FakeAPI()
    hit=E4.search("slider crank linkage",get_json=fake)[0]
    page=E4.fetch_page(hit,get_json=fake)
    record=E4.derive_evidence(page)
    for s in record["evidence_spans"]:
        assert s["text"] in page["plain_text"]
        assert s["supported"] is True
    joints={r["relation"] for r in record["candidate_relations"]}
    assert "hinged_to" in joints
    assert "slides_in" in joints
    spans={x["id"] for x in record["evidence_spans"]}
    assert all(set(rel["supported_span_ids"])<=spans
               for rel in record["candidate_relations"])
    assert record["excerpts_precurated"] is False
    assert record["human_review_required"] and not record["dimensions_bound_to_specific_joint"]


def test_quantities_are_only_literal_candidates_not_physical_parameters():
    fake=FakeAPI()
    page=E4.fetch_page(E4.search("slider crank linkage",get_json=fake)[0],
                        get_json=fake)
    r=E4.derive_evidence(page)
    items=r["candidate_quantities"]
    assert any(x["number"]==20 and x["unit_verbatim"]=="mm" for x in items)
    assert all(x["role_or_component_proven"] is False for x in items)
    assert all(x["usable_to_fill_mechanism_spec"] is False for x in items)
    assert not any(x["number"]==2012 for x in items)


def test_corrupted_text_or_revision_cannot_pretend_source_provenance():
    fake=FakeAPI()
    p=E4.fetch_page({"pageid":91,"title":"Slider-crank linkage"},get_json=fake)
    bad=copy.deepcopy(p);bad["plain_text"]="Pistons invented this text."
    with pytest.raises(ValueError,match="E4-FONTE-HASH_TEXTO"):
        E4.derive_evidence(bad)
    bad=copy.deepcopy(p);bad["revid"]="1981"
    with pytest.raises(ValueError,match="E4-FONTE-REVISAO"):
        E4.derive_evidence(bad)
    bad=copy.deepcopy(p);bad["source_url"]="https://example.org/specs"
    with pytest.raises(ValueError,match="E4-FONTE-ORIGEM"):
        E4.derive_evidence(bad)


def test_search_is_not_authority_to_assign_forged_pageid():
    fake=FakeAPI(mode="badid")
    r=E4.discover("slider crank linkage",__import__("tempfile").mkdtemp(),
                  get_json=fake)
    assert len(r["pages"])==1
    assert len(r["blocked_pages"])==1
    assert r["blocked_pages"][0]["pageid"]==92
    assert "PAGINA_NAO_COMPROVADA" in r["blocked_pages"][0]["reason"]


@pytest.mark.parametrize("query",(
    "x", "http://example.com", "four/bar", "quick$return",
    "this query contains far too many words for the limit now",
    "cat"*60,"gear; DROP TABLE","",
))
def test_untrusted_queries_rejected(query):
    with pytest.raises(ValueError,match="E4-FONTE-CONSULTA"):
        E4.validate_query(query)


def test_no_results_stays_blocked_and_not_an_engineering_claim(tmp_path):
    def none(params):
        if "srsearch" in params:return {"query":{"search":[]}}
        raise AssertionError("Page fetch must never be called")
    r=E4.discover("galaxy hinge mechanism",tmp_path,get_json=none)
    assert r["pages"]==[]
    assert r["status"]=="MOCKED_DISCOVERY_NO_LIVE_CLAIM"
    assert r["source_to_spec_auto"] is False


def test_fake_redirect_api_error_and_invalid_schema_fail_closed(tmp_path):
    for response in (
        {"error":{"code":"ratelimited"}},
        {"query":{"search":"a document"}},
        {"query":{"search":[{"ns":0,"pageid":True,"title":"Fake"}]}}
    ):
        def bad(_):return response
        r=E4.discover("whitworth quick return",tmp_path,get_json=bad)
        assert r["pages"]==[]
        assert not r["real_network_verified"]
        assert not r["render_allowed"]


def test_numeric_words_without_units_do_not_fill_specs():
    p={"pageid":12,"revid":24,"title":"Example",
       "plain_text":("The crank angle is 30 ticks and the gear has 20 teeth. "
                     "A transmission can rotate a lever without any geometry. ")*3,
       "source_url":"https://en.wikipedia.org/wiki/Example"}
    p["text_sha256"]=hashlib.sha256(p["plain_text"].encode()).hexdigest()
    r=E4.derive_evidence(p)
    assert r["candidate_quantities"]==[]
    assert r["mechanism_spec_generated"] is False
    assert r["publish"] is False
