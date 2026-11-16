# V3.1 — Arquitetura (diretor automático, biblioteca, memória)

## Fluxo (MOTOR_VISUAL=v3)

```
pesquisa → fatos e fontes → acervo do vídeo ──┐            (src/roteiro.py, src/acervo.py; contratos V2.4)
                                              ▼
roteiro definitivo ─► biblioteca global (cataloga + recupera mídia de outros vídeos)      src/v3/biblioteca.py
                    ─► contexto recuperado: receitas aprovadas/testadas, erros pertinentes,
                       regras aprovadas, composições viáveis, licenças                       src/v3/pipeline.py::montar_prompt
                    ─► STORYBOARD PELO MODELO (1 chamada; ≤ 1 correção dirigida)            storyboard_automatico
                    ─► validação por código (sem IA)                                         validar_storyboard + diretor.validar
                    ─► regiões (visão só para objeto inédito naquele sha)                    Biblioteca.localizar
                    ─► narração → tempos da fala alinhada                                    src/voz.py, aplicar_tempos
                    ─► montagem dos planos                                                   src/v2/diretor.py::montar
                    ─► prévia por quadros (sem MP4) → MP4                                    previa_quadros, src/render/render.py
                    ─► fiscal técnico + editorial (bloqueio / revisão / estética)             src/v3/fiscal_editorial.py
                    ─► registro para feedback (folha de contato, CSV por plano)              docs/memoria/feedback.jsonl
```

Gates: crítico sem plano válido, número fora da pesquisa, mecanismo crítico em cartão/foto de contexto, licença não
liberada, loudness/resolução/duração fora → **bloqueio** (sem aprovação). Plano não-crítico inválido sai e o vizinho cobre.

## Decisões
- **Renderizador mantido** (palco V2 + FFmpeg). A falta era de decisão, não de desenho (V3 §2). Remotion não entra.
- **Modelo do diretor:** Claude (assinatura, mesmo modelo do roteiro) por padrão; se falhar, 1 chamada no Gemini
  grátis (registrada). `DIRETOR_MODELO=gemini` força o gratuito.
- **Prompt pequeno:** só o que foi recuperado para o tema/tipos de acontecimento (≈ 17 mil caracteres no Ever Given).
- **Memória ≠ treino.** Receitas, erros e regras são arquivos versionados com estado e evidência; só `aprovado` vira
  boa prática no prompt. Nenhum peso de modelo muda.
- **Biblioteca:** SQLite + armazém por sha256 fora do Git; manifesto JSONL versionável; durabilidade = URL de origem +
  sha (re-download verificado). Remoto desativado — não há destino aprovado. Candidato gratuito para aprovar: Releases
  do repositório privado `coringa-cofre` (cifrado), ou Git LFS (cota de 1 GB). O cache do Actions **não** é armazenamento.
