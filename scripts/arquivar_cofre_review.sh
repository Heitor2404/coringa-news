#!/usr/bin/env bash
# Archive only local review files in the already-authorized private repository.
set -euo pipefail
repo=Heitor2404/coringa-cofre
tag="${1:?review tag required}"
shift
[[ "$tag" =~ ^review-[a-z0-9-]+$ ]] || exit 1
[[ $# -gt 0 ]] || exit 1
[[ -n "${GH_TOKEN:-}" ]] || { echo "COFRE_TOKEN ausente"; exit 1; }
# Never use fallback credentials, an alternate repo or a public destination.
[[ "$(gh api "repos/$repo" --jq '.private and (.id == 1454059520)')" == true ]] || { echo "Cofre privado não confirmado"; exit 1; }
for file in "$@"; do
  [[ -f "$file" && -s "$file" ]] || { echo "Arquivo ausente"; exit 1; }
done
# A checkpoint without its discovery index is an unusable investment.
python -m scripts.validar_arquivo_documental "$@"
if gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then
  echo "Release de revisão já existe; não sobrescrever"
  exit 1
fi
gh release create "$tag" "$@" --repo "$repo" --draft --title "Revisão documental privada $tag" --notes "Arquivos de trabalho para revisão humana. Não publicados em redes." >/dev/null
echo "COFRE: arquivos anexados a release privada em rascunho"
