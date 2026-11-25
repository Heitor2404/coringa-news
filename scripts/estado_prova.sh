#!/usr/bin/env bash
# Executa uma prova obrigatória e registra APROVADA / REPROVADA / BLOQUEADA (exit 77 = acesso/infraestrutura).
# Nunca deixa uma prova obrigatória "verde" sem ter rodado: o resumo final (scripts/resumo_provas.py) marca
# NAO_EXECUTADA toda prova esperada sem registro e reprova o job.
set -u
nome="$1"; shift
mkdir -p "${PROVAS_DIR:-provas}"
set +e
"$@"
rc=$?
set -e
case "$rc" in
  0) estado=APROVADA ;;
  77) estado=BLOQUEADA ;;
  *) estado=REPROVADA ;;
esac
printf '%s\t%s\t%s\n' "$nome" "$estado" "$rc" > "${PROVAS_DIR:-provas}/$nome.tsv"
echo "PROVA $nome $estado (rc=$rc)"
exit 0
