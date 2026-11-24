"""Convert actual E35 and E12 reports into separate private planning proofs.
Never use E12 linkage as fallback for the E35 topic. No fabricated evidence.
"""
import argparse
import json
from pathlib import Path
from . import rota_explicativa_e40 as R
from . import importador_juntas_json_e12 as E12


def cad_e35(report):
    escolha=report["escolha"]
    gates=report["gates"]
    sigs=[a["assinatura"] for c in report["candidatos"] if c.get("url")==escolha["url"]
          for a in c.get("analises",[]) if a.get("arquivo")==escolha["arquivo"]
          and a.get("sha256")==escolha["sha256"] and a.get("assinatura",{}).get("confirmada") is True]
    if len(sigs)!=1:
        raise ValueError("E40-E35-IDENTIDADE")
    return dict(tipo="cad_real",alvo=report["consulta"],identidade_verificada=True,
         fonte_url=escolha["url"],fonte_sha256=escolha["sha256"],
         licenca_candidata=escolha["licenca"]["classe"],
         juntas_fundamentadas=not bool(report["contrato"].get("hipoteses")),
         movimento_fundamentado=bool(report.get("solver")),
         estado=gates["estado"],verificacao_contato=gates["verificacao_contato"],
         # Unknown is not false.
         sobreposicao_inicial_fonte=None)


def esquemas_e12(manifest,report):
    if (report.get("schema")!="coringa-e12-second-origin-kinematics-v1"
        or report.get("publish") is not False
        or report.get("source_commit")!=manifest["source_commit"]
        or report.get("source_repository")!=manifest["source_repository"]):
        raise ValueError("E40-E12-RELATORIO")
    source_files={f["path"]:f["blob_sha1"] for f in manifest["files"]}
    out=[]
    for c in report["source_cases"]:
        p=c["source_path"]
        if (c.get("status")!="PASS_SOURCE_JSON_TO_COMMON_SOLVER"
            or c.get("source_live") is not True or c.get("source_provenance_verified") is not True
            or c.get("license_verified") is not True or c.get("source_commit")!=manifest["source_commit"]
            or c.get("source_blob_sha1")!=source_files.get(p)
            or c.get("jacobian_full_rank") is not True or c.get("real_CAD_part_contours_imported") is not False
            or c.get("max_residual_m",float("inf"))>1e-7):
            continue
        url="https://github.com/"+manifest["source_repository"]+"/blob/"+manifest["source_commit"]+"/"+p
        out.append(dict(tipo="esquema_cinematico_2d",alvo="cinematica_declarada:"+p,
            identidade_verificada=True,fonte_sha256=c["source_sha256"],fonte_url=url,
            licenca_candidata="permissiva",juntas_fundamentadas=True,movimento_fundamentado=True,
            apenas_principio=True,solver_verificado=True))
    return out


def provar(e35,manifest):
    report,_,_=E12.audit_manifest(manifest,network_verified=True,samples=121)
    cad=cad_e35(e35); esquemas=esquemas_e12(manifest,report)
    if not esquemas:
        raise ValueError("E40-SEM_ESQUEMA_REAL")
    principal=R.planejar([cad]+esquemas,alvo=cad["alvo"])
    if principal["decisao"] is not None:
        raise ValueError("E40-ALTERNATIVA_ERRADA")
    outros=[R.planejar([e],alvo=e["alvo"]) for e in esquemas]
    if not all(p["decisao"] for p in outros):
        raise ValueError("E40-ESQUEMA_NAO_ELEGIVEL")
    return dict(cad_reprovado=principal,esquemas_independentes=outros,
        fonte_e12=report,publish=False,visual_approved=False,
        natureza="prova de roteamento, sem nova renderizacao")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("e35")
    p.add_argument("manifest")
    p.add_argument("saida")
    a=p.parse_args()
    r=provar(json.loads(Path(a.e35).read_text()),json.loads(Path(a.manifest).read_text()))
    Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print("E40-REAL",json.dumps(dict(cad=r["cad_reprovado"],esquemas=len(r["esquemas_independentes"])),ensure_ascii=False))
