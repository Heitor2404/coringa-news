# Componentes editoriais (Etapa 3, frente B) — isolados

Estes cinco componentes são para aprovação visual e não estão ligados ao template principal:
- abertura;
- revelação;
- mapa;
- etiqueta;
- encerramento.

Eles seguem o mesmo contrato do template:
- `EDITORIAL.carregar(spec)` monta o componente;
- `seek(t)` desenha o quadro `t` de forma determinística.

A origem e as licenças estão em [NOTICE.md](NOTICE.md).

Para gerar a prévia (quadros, folha e MP4 em `saida/prototipos/ed_<nome>/`):

```
python prototipos/editorial/previa.py specs/mapa.json [--quadros 1,3] [--sem-video] [--zonas]
```

Os testes ficam em `tests/test_prototipo_editorial.py`.
