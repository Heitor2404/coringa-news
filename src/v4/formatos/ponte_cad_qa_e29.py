"""Select an independently accepted model from a multi-model private QA.

Reuses the E28 stage bridge. No renderer, topology or editorial case by name.
A batch identifier is input data; its model must have passed execution and
external validation. This is not approval for publication.
"""
import argparse
import json
import tempfile
from pathlib import Path
from . import ponte_cad_editorial_e28 as E


def selecionar(qa, modelo_id):
    if not isinstance(modelo_id,str) or not modelo_id:
        raise ValueError("E29-ID")
    models=qa.get("modelos")
    if not isinstance(models,list):
        raise ValueError("E29-LOTE")
    found=[m for m in models if isinstance(m,dict) and m.get("id")==modelo_id]
    if len(found)!=1:
        raise ValueError("E29-MODELO_AUSENTE_OU_AMBIGUO")
    m=found[0]
    if (m.get("estado_execucao")!="PASS" or m.get("validacao_externa")!="APROVADO"
            or m.get("estado")!="VALIDADO_TECNICAMENTE_SEM_HOMOLOGACAO_VISUAL"
            or m.get("liberado_para_publicacao") is not False
            or m.get("publish") is not False or m.get("visual_approved") is not False):
        raise ValueError("E29-SEM_VALIDACAO_EXTERNA")
    if not isinstance(m.get("palco_cad"),dict):
        raise ValueError("E29-SEM_PALCO")
    return m


def preparar(qa, modelo_id, public_root, output):
    qa=Path(qa).resolve()
    m=selecionar(json.loads(qa.read_text()),modelo_id)
    # Temporary verified selection in the same directory as the stage;
    # never modify batch QA. E28 rechecks file hash and decodes the bytes.
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",
                                      suffix=".json",dir=qa.parent) as f:
        json.dump(m,f,ensure_ascii=False)
        f.flush()
        return E.preparar(f.name,public_root,output)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("qa")
    p.add_argument("modelo_id")
    p.add_argument("public")
    p.add_argument("output")
    a=p.parse_args()
    preparar(a.qa,a.modelo_id,a.public,a.output)
