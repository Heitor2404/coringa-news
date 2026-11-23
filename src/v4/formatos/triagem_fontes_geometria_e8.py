"""E8: independent open-source geometry source catalog with revision/rights proof.

Bounded multi-repo discovery, not arbitrary web browsing. Verifies the
license and exact blobs, then classifies if data has complete joint geometry.
An MIT README with preset lengths is not a transferable MechanismSpec.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
from pathlib import Path
from urllib.request import Request, build_opener, HTTPSHandler

from src.v4.formatos.importador_geometria_e7 import git_blob_sha1, source_geometry
from src.v4.formatos.ingestao_evidencias_f16 import NoRedirect

SCHEMA="coringa-e8-multi-repo-source-registry-v1"
OUT_SCHEMA="coringa-e8-source-triage-v1"
REPO=re.compile(r"^[A-Za-z0-9_.-]{1,48}/[A-Za-z0-9_.-]{1,80}$")
COMMIT=re.compile(r"^[a-f0-9]{40}$")
BLOB=re.compile(r"^[a-f0-9]{40}$")
PATH=re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+){0,7}$")
MAX_BYTES=100000
ORIGIN="https://raw.githubusercontent.com"

def fail(reason):raise ValueError("E8-FONTE-"+reason)

def validate_registry(registry):
    if (not isinstance(registry,dict)
       or registry.get("schema")!=SCHEMA
       or registry.get("scope")!="bounded_catalog_not_open_world_github_discovery"
       or registry.get("publish") is not False):fail("MANIFESTO")
    sources=registry.get("sources")
    if not isinstance(sources,list) or not 2<=len(sources)<=10:fail("QUANTIDADE")
    names=set();repo_commits=set()
    for item in sources:
        if not isinstance(item,dict) or set(item)!={
            "id","repository","commit","license_path","license_blob_sha1","samples"
        }:fail("FORMATO")
        rid=item["id"];repository=item["repository"];commit=item["commit"]
        if (not isinstance(rid,str) or not re.fullmatch(r"[a-z][a-z0-9_]{2,42}",rid)
           or not isinstance(repository,str) or not REPO.fullmatch(repository)
           or not isinstance(commit,str) or not COMMIT.fullmatch(commit)):
            fail("IDENTIDADE")
        if rid in names or (repository,commit) in repo_commits:fail("DUPLICADO")
        names.add(rid);repo_commits.add((repository,commit))
        if (item["license_path"]!="LICENSE"
            or not isinstance(item["license_blob_sha1"],str)
            or not BLOB.fullmatch(item["license_blob_sha1"])):
            fail("LICENCA")
        files=item["samples"]
        if not isinstance(files,list) or not 1<=len(files)<=12:
            fail("AMOSTRAS")
        paths=set()
        for record in files:
            if (not isinstance(record,dict)
                or set(record)!={"path","blob_sha1"}
                or not isinstance(record["path"],str)
                or not PATH.fullmatch(record["path"])
                or not record["path"].endswith((".csv",".json",".md"))
                or not isinstance(record["blob_sha1"],str)
                or not BLOB.fullmatch(record["blob_sha1"])):
                fail("ARQUIVO")
            if record["path"] in paths:fail("DUPLICADO")
            paths.add(record["path"])
    return True

def fetch(repository,commit,path):
    if (not isinstance(repository,str) or not REPO.fullmatch(repository)
        or not isinstance(commit,str) or not COMMIT.fullmatch(commit)
        or not isinstance(path,str) or not PATH.fullmatch(path)):
        fail("CAMINHO")
    url=f"{ORIGIN}/{repository}/{commit}/{path}"
    req=Request(url,headers={
      "User-Agent":"Coringa-E8-Source-Provenance/1.0 (+github.com/Heitor2404/coringa-news)",
      "Accept":"text/plain","Accept-Encoding":"identity",
    })
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req,timeout=12) as response:
            if response.status!=200 or response.url!=url:
                fail("HTTP_OU_REDIRECT")
            content=response.read(MAX_BYTES+1)
    except (OSError,TimeoutError) as exc:
        fail("FETCH_"+type(exc).__name__)
    if not content or len(content)>MAX_BYTES:fail("TAMANHO")
    return content

def classify(content,path):
    if not isinstance(content,bytes) or not isinstance(path,str):
        fail("CONTEUDO")
    try:text=content.decode("utf-8-sig")
    except UnicodeDecodeError:fail("UTF8")
    if path.endswith(".csv") and text.lstrip().startswith("LinkageDesign,1"):
        try:
            spec,info=source_geometry(content)
            return {"capability":"STRUCTURED_PLANAR_SOURCE",
                    "can_build_mechanism_spec_without_named_template":True,
                    "body_count":info["converted_body_count"],
                    "joint_count":info["converted_joint_count"],
                    "geometry_constraints_verified":info["source_geometry_satisfied_constraints"],
                    "kinematic_trajectory_not_yet_tested":True}
        except ValueError as exc:
            return {"capability":"STRUCTURED_SOURCE_REJECTED_BY_GEOMETRY_GATE",
                    "can_build_mechanism_spec_without_named_template":False,
                    "reason":str(exc)[:140]}
    if path.endswith(".json"):
        try:doc=json.loads(text)
        except (ValueError,UnicodeError):fail("JSON")
        # A reference can assert output positions, but cannot create the
        # actual bodies and joint topology without explicit ground/links.
        if (isinstance(doc,dict) and isinstance(doc.get("phases"),list)
            and any(k.endswith("_B") or k.endswith("_P") for k in doc)):
            return {"capability":"INDEPENDENT_KINEMATIC_ORACLE_ONLY",
                    "can_build_mechanism_spec_without_named_template":False,
                    "source_has_trajectory_samples":True,
                    "numeric_samples_are_not_joint_anchors":True}
    if path.endswith(".md") and ((chr(96)*3)+"mechanism") in text and "type:" in text:
        return {"capability":"PARAMETRIC_PRESET_NO_EXPLICIT_JOINT_ANCHORS",
                "can_build_mechanism_spec_without_named_template":False,
                "joint_type_implied_by_preset_name_only":True,
                "no_fully_explicit_body_to_body_connections":True}
    return {"capability":"UNRECOGNIZED_SOURCE_FORMAT",
            "can_build_mechanism_spec_without_named_template":False}

def audit(registry,*,getter=fetch,network_verified=False):
    validate_registry(registry)
    if network_verified and getter is not fetch:fail("MOCK_NAO_E_LIVE")
    reports=[]
    for item in registry["sources"]:
        repo=item["repository"];commit=item["commit"]
        license_bytes=getter(repo,commit,item["license_path"])
        if git_blob_sha1(license_bytes)!=item["license_blob_sha1"]:
            fail("LICENCA_HASH")
        if not license_bytes.decode("utf8").startswith("MIT License\n"):
            fail("LICENCA_CONTEUDO")
        rows=[]
        for entry in item["samples"]:
            content=getter(repo,commit,entry["path"])
            if git_blob_sha1(content)!=entry["blob_sha1"]:
                fail("ARQUIVO_HASH")
            capability=classify(content,entry["path"])
            rows.append({
              "path":entry["path"],
              "git_blob_sha1_verified":entry["blob_sha1"],
              "sha256":hashlib.sha256(content).hexdigest(),
              "source_size_bytes":len(content),
              **capability,
              "industrial_machine_identity_verified":False,
              "media_asset_reused":False,
              "license_inheritance_review_required":True,
              "publish":False,
            })
        reports.append({
          "id":item["id"],"repository":repo,"commit":commit,
          "license":"MIT","license_exact_blob_verified":True,
          "license_blob_sha1":item["license_blob_sha1"],
          "source_files":rows,
          "runtime_source_verified":bool(network_verified),
          "media_reuse_proven":False,
        })
    total=sum(len(x["source_files"]) for x in reports)
    suitable=sum(f["can_build_mechanism_spec_without_named_template"]
                 for x in reports for f in x["source_files"])
    return {
      "schema":OUT_SCHEMA,
      "status":"PROVENANCE_CONFIRMED_CAPABILITY_GATED" if network_verified
               else "MOCKED_SOURCE_TRIAGE_NOT_LIVE",
      "source_count":len(reports),
      "source_sample_files":total,
      "source_files_with_complete_anchor_geometry":suitable,
      "unusable_sample_files":total-suitable,
      "repositories":[x["repository"] for x in reports],
      "source_checks":reports,
      "open_internet_topic_discovery":False,
      "unlisted_urls_crawled":False,
      "source_license":"MIT_per_repository_exact_license_blob",
      "geometry_inference_from_prose":False,
      "independent_review_complete":False,
      "auto_publish":False,"visual_approved":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    record=audit(json.loads(args.registry.read_text("utf8")),
                 network_verified=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf8")
    print(json.dumps({"status":record["status"],
      "source_count":record["source_count"],
      "samples":record["source_sample_files"],
      "usable_geometry":record["source_files_with_complete_anchor_geometry"],
      "automatic_topic_discovery":False,"publish":False},ensure_ascii=False))

if __name__=="__main__":main()
