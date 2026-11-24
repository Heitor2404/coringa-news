"""Bounded public CAD discovery. Search hits and SPDX metadata are candidates,
not evidence of mechanical identity, commercial rights or verified joints.
No credentials, arbitrary URLs, redirects, execution or asset downloads.
Agent-Reach JSON is optional input, never an instruction or proof.
"""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

REPO=re.compile(r"[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}\Z")
SHA=re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES=4_000_000
GEOM={".step",".stp",".iges",".igs",".stl",".obj",".dxf",".svg",".fcstd",".glb"}
ART={".urdf",".mjcf",".sdf",".srdf"}

class SemRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None

class PesquisaErro(ValueError):
    pass

def fail(code):
    raise PesquisaErro("E34-"+code)

def query(q):
    if not isinstance(q,str) or not 4<=len(q)<=100 or not re.fullmatch(r"[\w .-]+",q):
        fail("CONSULTA")
    return q.strip()

def repo_id(s):
    if not isinstance(s,str) or not REPO.fullmatch(s) or any(x in (".","..") for x in s.split("/")):
        fail("REPO")
    return s

def get(path):
    # Only internally constructed REST paths; no auth even if env has tokens.
    if not path.startswith(("/search/repositories?","/repos/")) or "#" in path or "\\" in path:
        fail("ENDPOINT")
    req=Request("https://api.github.com"+path,headers={
        "Accept":"application/vnd.github+json","User-Agent":"Coringa-CAD-research/1",
        "X-GitHub-Api-Version":"2022-11-28"})
    try:
        with build_opener(SemRedirect()).open(req,timeout=15) as r:
            raw=r.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            fail("RESPOSTA_GRANDE")
        return json.loads(raw)
    except HTTPError as e:
        if e.code in (403,429):
            # Do not infer cause from status alone; preserve rate headers.
            remaining=e.headers.get("X-RateLimit-Remaining")
            retry=e.headers.get("Retry-After")
            reset=e.headers.get("X-RateLimit-Reset")
            err=PesquisaErro("E34-BLOQUEADO_OU_LIMITADO")
            err.http=dict(status=e.code,remaining=remaining,retry_after=retry,reset=reset)
            raise err from None
        fail("HTTP_"+str(e.code))
    except (URLError,TimeoutError):
        fail("REDE")
    except (UnicodeError,json.JSONDecodeError):
        fail("JSON")

def search(q,limit=4,getter=get):
    q=query(q)
    if type(limit) is not int or not 1<=limit<=5:
        fail("LIMITE")
    r=getter("/search/repositories?"+urlencode({"q":q,"per_page":limit}))
    if not isinstance(r,dict) or not isinstance(r.get("items"),list):
        fail("RESULTADO")
    ids=[]
    for item in r["items"][:limit]:
        if item.get("private") is True or item.get("archived") is True:
            continue
        rid=repo_id(item.get("full_name"))
        if item.get("html_url")!="https://github.com/"+rid:
            fail("URL")
        if rid not in ids:
            ids.append(rid)
    return ids

def agent_reach_ids(envelope):
    if (not isinstance(envelope,dict) or envelope.get("schema_version")!=1
        or envelope.get("channel")!="github" or envelope.get("action")!="search"):
        fail("AGENT_REACH_SCHEMA")
    if envelope.get("ok") is not True or envelope.get("error") is not None:
        fail("AGENT_REACH_NAO_OK")
    items=envelope.get("items")
    if not isinstance(items,list) or len(items)>5:
        fail("AGENT_REACH_ITENS")
    out=[]
    for item in items:
        rid=repo_id(item.get("title"))
        if item.get("url")!="https://github.com/"+rid:
            fail("AGENT_REACH_URL")
        if rid not in out:
            out.append(rid)
    return out

def inspect(rid,getter=get):
    rid=repo_id(rid)
    prefix="/repos/"+rid
    info=getter(prefix)
    if info.get("private") is not False or info.get("full_name","").lower()!=rid.lower():
        fail("REPO_NAO_PUBLICO")
    branch=info.get("default_branch")
    if not isinstance(branch,str) or not branch or len(branch)>200:
        fail("BRANCH")
    commit=getter(prefix+"/commits?"+urlencode({"sha":branch,"per_page":1}))
    if not isinstance(commit,list) or len(commit)!=1:
        fail("COMMIT")
    rev=commit[0].get("sha")
    tree=commit[0].get("commit",{}).get("tree",{}).get("sha")
    if not isinstance(rev,str) or not SHA.fullmatch(rev) or not isinstance(tree,str) or not SHA.fullmatch(tree):
        fail("REVISAO")
    tr=getter(prefix+"/git/trees/"+tree+"?recursive=1")
    if tr.get("sha")!=tree or tr.get("truncated") is not False or not isinstance(tr.get("tree"),list):
        fail("ARVORE_INCOMPLETA")
    geom=[];art=[]
    for b in tr["tree"]:
        if b.get("type")!="blob" or b.get("mode") not in ("100644","100755"):
            continue
        p=b.get("path","")
        if not isinstance(p,str) or len(p)>400 or not p or any(x in ("","..",".") for x in p.split("/")) or "\\" in p:
            continue
        suffix=Path(p).suffix.lower()
        if suffix not in GEOM|ART:
            continue
        sha=b.get("sha")
        if not isinstance(sha,str) or not SHA.fullmatch(sha):
            fail("BLOB")
        (art if suffix in ART else geom).append(dict(path=p,git_blob_sha1=sha,size=b.get("size")))
    lic=None
    try:
        x=getter(prefix+"/license?"+urlencode({"ref":rev}))
        if x.get("encoding")!="base64" or not isinstance(x.get("content"),str):
            fail("LICENCA_FORMATO")
        raw=base64.b64decode("".join(x["content"].split()),validate=True)
        if not raw or len(raw)>100_000:
            fail("LICENCA_TAMANHO")
        blob=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        if blob!=x.get("sha"):
            fail("LICENCA_BLOB")
        path=x.get("path")
        if not isinstance(path,str) or not any(b.get("path")==path and b.get("sha")==blob for b in tr["tree"]):
            fail("LICENCA_FORA_DA_REVISAO")
        lic=dict(path=path,git_blob_sha1=blob,sha256=hashlib.sha256(raw).hexdigest(),
                 spdx_metadata=(x.get("license") or {}).get("spdx_id"))
    except PesquisaErro as e:
        if str(e)!="E34-HTTP_404":
            raise
    return dict(repository=rid,url="https://github.com/"+rid,revision=rev,tree_sha1=tree,
                geometry_candidates=sorted(geom,key=lambda x:x["path"])[:40],
                articulation_candidates=sorted(art,key=lambda x:x["path"])[:40],
                geometry_count=len(geom),articulation_count=len(art),license_candidate=lic,
                identity="NAO_VERIFICADA",rights="NAO_VERIFICADOS",
                joints="NAO_VERIFICADAS",publish=False)

def discover(q,limit=4,getter=get,reach=None):
    q=query(q)
    ids=search(q,limit,getter) if reach is None else agent_reach_ids(reach)
    found=[];blocked=[]
    for rid in ids:
        stage="metadata"
        def tracked(path):
            nonlocal stage
            stage=("revision" if "/commits?" in path else "tree" if "/git/trees/" in path
                   else "license" if "/license?" in path else "metadata")
            return getter(path)
        try:
            found.append(inspect(rid,tracked))
        except PesquisaErro as e:
            blocked.append(dict(repository=rid,stage=stage,reason=str(e),http=getattr(e,"http",None)))
            if str(e)=="E34-BLOQUEADO_OU_LIMITADO":
                break
    # Prioritize structured joint file candidates, not name or stars.
    found.sort(key=lambda x:(bool(x["articulation_count"]),bool(x["geometry_count"]),
                             bool(x["license_candidate"])),reverse=True)
    return dict(schema="coringa.pesquisa.cad.v1",query=q,
                backend="github_public" if reach is None else "agent_reach_envelope_then_github_public",
                discovered_ids=ids,candidates=found,blocked=blocked,complete_search=False,publish=False)

def discover_many(queries,limit=4,getter=get):
    reports=[];stop=False
    for q in queries:
        q=query(q)
        if stop:
            reports.append(dict(schema="coringa.pesquisa.cad.v1",query=q,discovered_ids=[],
                    candidates=[],blocked=[dict(reason="E34-NAO_EXECUTADA_APOS_BLOQUEIO")],
                    complete_search=False,publish=False))
            continue
        try:
            r=discover(q,limit,getter)
        except PesquisaErro as e:
            r=dict(schema="coringa.pesquisa.cad.v1",query=q,discovered_ids=[],candidates=[],
                    blocked=[dict(stage="search",reason=str(e),http=getattr(e,"http",None))],
                    complete_search=False,publish=False)
        reports.append(r)
        stop=any(x["reason"]=="E34-BLOQUEADO_OU_LIMITADO" for x in r["blocked"])
    return reports


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("query")
    p.add_argument("output")
    p.add_argument("--limit",type=int,default=4)
    p.add_argument("--agent-reach-json")
    p.add_argument("--also",action="append",default=[])
    a=p.parse_args()
    if a.also:
        if a.agent_reach_json:
            fail("LOTE_AGENT_REACH_NAO_SUPORTADO")
        reports=discover_many([a.query]+a.also,a.limit)
        Path(a.output).write_text(json.dumps(reports,ensure_ascii=False,indent=2))
        print(json.dumps(reports,ensure_ascii=False))
        raise SystemExit(0 if all(x["candidates"] for x in reports) else 2)
    reach=json.loads(Path(a.agent_reach_json).read_text()) if a.agent_reach_json else None
    try:
        r=discover(a.query,a.limit,reach=reach)
    except PesquisaErro as e:
        r=dict(schema="coringa.pesquisa.cad.v1",query=a.query,candidates=[],blocked=[{"reason":str(e)}],
               complete_search=False,publish=False)
    Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(r,ensure_ascii=False))
    if not r["candidates"]:
        raise SystemExit(2)
