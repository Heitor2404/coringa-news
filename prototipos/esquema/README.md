# Protótipo ESQUEMA + clímax (Etapa 3) — isolado

Não está ligado ao template principal (`src/render/template.html`). Serve para aprovação visual antes da integração.

- `motor.js` — motor genérico: lê uma spec JSON e desenha o quadro `t` do zero com `seek(t)`, de forma determinística, igual ao template.
  - **Primitivas:**
    - biologia: `cromatoforo`, `pele`, `neuronio`, `nervo`;
    - física/tecnologia: `raio`, `molecula` (inclusive água), `espalhamento`, `fonte_luz`, `faixa`, `campo`, `olho`, `fibra`;
    - genéricas: `seta`, `brilho`, `texto`.
  - Tipo ou propriedade desconhecidos são rejeitados.
  - **Rótulos** com linha-guia, em JBM de 24–26 px, sem escalar com o desenho.
  - **Passos** sincronizados com a fala. O `destaque` escurece o resto da cena.
- `pagina.html` — o mesmo fundo, as mesmas fontes e os mesmos tokens do Coringa.
- `specs/`
  - `cromatoforo.json` — o mecanismo, em 5 passos;
  - `climax_polvo.json` — revelação com demonstração;
  - `ceu_azul.json` — física;
  - `micro_ondas.json` — tecnologia.

  Cada spec lista os `fatos` em que o desenho se apoia.
- `previa.py` — gera quadros, uma folha de contato e um MP4 curto em `saida/prototipos/<id>/`.

  ```
  python prototipos/esquema/previa.py specs/cromatoforo.json [--quadros 1,2.5] [--sem-video] [--zonas]
  ```
