"""Reproduz planos REAIS de cache com tempos medidos, sem chamar IA/voz; recortes privados."""
import hashlib,json,subprocess
from pathlib import Path
from src.v4.formatos import diretor_visual_e202 as D, ciclo_e202 as C
out=Path("qa_e204");out.mkdir(exist_ok=True)
cases=json.load(open("benchmarks/e202/temas_ineditos.json"))["cases"]
cache=Path("benchmarks/e202/cache")
for caso in cases:
    cid=caso["id"]; matches=[]
    for p in cache.glob("*.json"):
        raw=json.loads(p.read_text());plan=raw["json"]
        if not isinstance(plan.get("cenas"),list) or not plan["cenas"]:continue
        try:
            falas=C._falas(plan);h=hashlib.sha256("\n".join(falas).encode()).hexdigest()[:16]
            n=Path(f"benchmarks/e202/narracao/{cid}-{h}.json")
            if n.is_file():matches.append((raw.get("data",""),p,plan,n))
        except (KeyError,TypeError):continue
    assert matches,cid
    _,p,plan,n=max(matches,key=lambda x:x[0])
    ndata=json.loads(n.read_text())
    f=D.filme({"plano":plan},caso,ndata["duracoes"],ndata["palavras"])
    props=f["props"];target=out/f"{cid}.mp4"
    pj=out/f"{cid}.props.json";pj.write_text(json.dumps(props,ensure_ascii=False))
    frames=min(240,int(props["duracao"]*30))
    cmd=["npx","--no-install","remotion","render","remotion/src/index.ts","FilmeEditorial",str(target.resolve()),f"--props={pj.resolve()}",f"--frames=0-{frames-1}","--codec=h264","--crf=20","--concurrency=2","--public-dir=remotion/public","--log=error"]
    subprocess.run(cmd,cwd="motor4",check=True)
    info=C.sondar(target)
    assert info["quadros"]==frames and info["largura"]==1080 and info["altura"]==1920
    C.folha(target,out/f"{cid}_folha.jpg")
    (out/f"{cid}_qa.json").write_text(json.dumps({"cache":p.name,"narracao":n.name,"origem":"replay sem voz","sonda":info,"geometria":[g for s in props["shots"] for g in D.geometria(s["scene_graph"],s["id"])]},ensure_ascii=False))
    print("E204-REPLAY",cid,info["quadros"],info["sha256"])
