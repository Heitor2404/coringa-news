---
name: coringa-acervo
description: Use ao trabalhar com mídia do Coringa — biblioteca global (SQLite + armazém por sha256), licenças, deduplicação, regiões de interesse, reuso entre vídeos, backup/limpeza.
---
# Acervo e Biblioteca Coringa

- Código: `src/v3/biblioteca.py` (global) sobre `src/acervo.py` (busca por vídeo) e `src/v2/acervo_v2.py` (pHash, licença).
- ID global estável `cm-<sha12>`; `a3` é só alias da produção (tabela `usos`).
- Antes de baixar: `Biblioteca.buscar(...)` (exclui IA e licença não comercial/indefinida). Mesmo sha = reuso; pHash ≤ 6 =
  variante (análises não são copiadas).
- Regiões de interesse presas ao sha: `Biblioteca.localizar` só chama a visão para objeto nunca pedido naquele arquivo.
- Licença: `classificar_licenca` → sim/nao/indefinido. **indefinido nunca é liberado.** NC e ND ficam fora (o vídeo recorta e anima).
- Durabilidade: banco e binários fora do Git; manifesto versionável (`exportar`/`importar`); cópia durável = URL de
  origem + sha (`recuperar` confere o hash). Remoto desativado até haver destino aprovado (docs/v3/BIBLIOTECA.md).
- CLI: `python -m src.v3.biblioteca buscar "termos" | verificar | limpar [--aplicar] | exportar F | importar F | backup PASTA`.
- Nunca use a mesma foto em planos seguidos nem mais de 2× no vídeo (ERR-007).

Testes: `python -m pytest -q tests/test_v3_biblioteca.py`.
