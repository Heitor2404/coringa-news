"""Galeria comparativa V2 × V2.1 (página privada). Lê o que as etapas já gravaram em saida/v21 e monta
saida/v21/galeria/index.html, que referencia imagens e vídeos por caminho relativo (publicação por arquivos).

Pré-requisitos: scripts/v2_capturar.py (antes/depois), src.v2.antes_depois (panama), src.v2.experimental,
src.v2.avaliacao_selecao, src.v2.avaliacao_fiscal e /home/claude/previas.py (prévias e temas).
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.v2 import auditoria_v21 as A  # noqa: E402

V = Path('saida/v21')
G = V / 'galeria'
e = html.escape


def _j(p, padrao=None):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:
        return padrao


def main():
    sel = _j(V / 'selecao_depois.json', {}); sel0 = _j(V / 'selecao_antes.json', {})
    fb = _j(V / 'fiscal_bench.json', {}); ex = _j(V / 'experimental' / 'relatorio.json', {})
    pan = _j(V / 'panama' / 'comparacoes.json', []); fpan = _j(V / 'panama' / 'antes_depois' / 'fiscal_v2_panama.json', {})
    temas = _j(G / 'temas.json', []); tempos_prev = _j(G / 'previas' / 'tempos.json', {})
    cat_a = _j(V / 'antes' / 'catalogo.json', {}); cat_d = _j(V / 'depois' / 'catalogo.json', {})
    res = A.resumo()
    cor = {'aprovado tecnicamente': '#3ccf8e', 'parcial': '#ffd21f', 'bloqueado': '#ff5a4d'}

    cards = []
    for a in A.AUDITORIA:
        c = a['id']
        ant = (G / 'img' / f'{c}__antes.jpg').exists()
        prev = G / 'previas' / f'{c}.mp4'
        campos = ''.join(f'<dt>{e(k.replace("_", " "))}</dt><dd>{e(str(a[k]))}</dd>' for k in A.CAMPOS[1:-1])
        seg = f"{(cat_a.get(c) or {}).get('segundos', '—')} s → {(cat_d.get(c) or {}).get('segundos', '—')} s"
        cards.append(f'''<article class="comp" data-estado="{e(a['estado'])}" id="c-{c.replace('.', '-')}">
  <header><h3>{e(c)}</h3><span class="tag" style="--c:{cor[a['estado']]}">{e(a['estado'])}</span><span class="t">captura {e(seg)}</span></header>
  <div class="lado"><b>V2</b>{f'<img loading="lazy" src="img/{c}__antes.jpg" alt="V2 {e(c)}">' if ant else '<p class="nova">composição nova na V2.1</p>'}</div>
  <div class="lado"><b>V2.1</b><img loading="lazy" src="img/{c}__depois.jpg" alt="V2.1 {e(c)}"></div>
  <p class="inst">instantes: 8% · 45% · 75% (máximo de informação) · 97%</p>
  {f'<video controls muted loop playsinline preload="none" src="previas/{c}.mp4"></video>' if prev.exists() else ''}
  <details><summary>auditoria (15 campos)</summary><dl>{campos}</dl></details>
</article>''')

    pan_html = ''.join(f'''<figure><img loading="lazy" src="img/panama_{x['t']:05.2f}.jpg" alt="{e(x['titulo'])}">
  <figcaption><b>{e(x['titulo'])}</b> · {x['t']:.1f} s · {e(x['comp'])}<br>{e(x['nota'])}</figcaption></figure>''' for x in pan)

    temas_html = ''
    for t in temas:
        caps = ''.join(f'<img loading="lazy" src="{e(p)}" alt="">' for p in t.get('capturas', []))
        vid = f'<video controls muted loop playsinline preload="none" src="{e(t["previa"])}"></video>' if t.get('previa') else ''
        temas_html += f'<article class="tema"><h3>{e(t["titulo"])}</h3><div class="caps">{caps}</div>{vid}<p class="t">problemas medidos: {len(t.get("problemas", []))} · erros: {len(t.get("erros", []))}</p></article>'

    def linhas_sel(lst):
        return ''.join(f'<tr class="{"ok" if x["passou"] else "xx"}"><td>{e(x["id"])}</td><td>{e(x.get("dominio") or x.get("testa", ""))}</td><td>{e(x["fala"])}</td><td>{e(x["escolha"])}</td><td>{e(", ".join(x["aceitaveis"]))}</td><td>{"✓" if x["passou"] else "✗"}</td></tr>' for x in lst)

    sinc = ex.get('sincronia', [])
    ecl = next((v for v in sinc if v.get('comp') == 'mecanismo.eclusa'), {}); rev = next((v for v in sinc if v.get('comp') == 'revelacao.surpresa'), {})
    leg = next((v for v in sinc if v.get('legenda')), {})
    crit = ''.join(f'<li>{"✓" if v else "✗"} {e(k.replace("_", " "))}</li>' for k, v in {**ecl.get('criterios', {}), **rev.get('criterios', {})}.items())
    fisc = ''.join(f'<tr><td>{e(a["categoria"])}</td><td>{e(a["codigo"])}</td><td>{"" if a["cena"] is None else a["cena"]}</td><td>{"" if a["instante"] is None else a["instante"]}</td><td>{e(a["problema"])}</td><td>{e(str(a["evidencia"])[:120])}</td><td>{e(a["gravidade"])}</td><td>{e(a["solucao"])}</td></tr>'
                   for a in ex.get('fiscal', {}).get('achados', []))
    bench = ''.join(f'<tr class="{"ok" if x["detectou"] and not x["falso_positivo"] else "xx"}"><td>{e(x["id"])}</td><td>{e(x["esperado"])}</td><td>{e(", ".join(x["acusou_no_defeito"]))}</td><td>{e(", ".join(x["acusou_no_correto"]) or "—")}</td><td>{e(str(x["evidencia"])[:90])}</td></tr>' for x in fb.get('casos', []))
    cenas_ex = ''.join(f'<tr><td>{c["k"]}</td><td>{e(c["comp"])}</td><td>{c["inicio"]:.2f}–{c["fim"]:.2f}</td><td>{e(c["fala"])}</td><td>{e(str(c["decisao"])[:90])}</td></tr>' for c in ex.get('cenas', []))

    pagina = f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coringa Explica — galeria V2 × V2.1</title>
<style>
:root{{--bg:#0d1017;--pn:#151a24;--tx:#e8eaf0;--mu:#9aa3b5;--am:#ffd21f;--ln:#262d3b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 18px 80px}}h1{{font-size:28px;margin:0 0 6px}}h2{{font-size:21px;margin:44px 0 12px;padding-top:10px;border-top:1px solid var(--ln)}}
h3{{font-size:16px;margin:0}}a{{color:var(--am)}}.mu{{color:var(--mu)}}.aviso{{background:#2a2410;border-left:4px solid var(--am);padding:10px 14px;margin:14px 0}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}}nav a{{background:var(--pn);padding:6px 10px;border-radius:6px;text-decoration:none;font-size:14px}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}}.kpi div{{background:var(--pn);padding:12px;border-radius:8px}}.kpi b{{display:block;font-size:24px;color:var(--am)}}
.filtros button{{background:var(--pn);color:var(--tx);border:1px solid var(--ln);border-radius:6px;padding:6px 12px;margin:0 6px 8px 0;cursor:pointer}}.filtros button.on{{border-color:var(--am);color:var(--am)}}
.comp,.tema{{background:var(--pn);border-radius:10px;padding:14px;margin:14px 0}}.comp header{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px}}
.tag{{border:1px solid var(--c);color:var(--c);border-radius:20px;padding:1px 10px;font-size:13px}}.t{{color:var(--mu);font-size:13px}}
.lado{{margin:6px 0}}.lado b{{display:inline-block;width:44px;color:var(--mu);font-size:13px;vertical-align:top}}.lado img{{width:calc(100% - 50px);max-width:1098px;border-radius:4px}}
.nova{{display:inline-block;color:var(--am)}}.inst{{color:var(--mu);font-size:12px;margin:2px 0 8px 50px}}video{{max-width:270px;width:100%;border-radius:6px;display:block;margin:8px 0}}
details{{margin-top:6px}}summary{{cursor:pointer;color:var(--am)}}dl{{display:grid;grid-template-columns:170px 1fr;gap:4px 12px;margin:10px 0 0}}dt{{color:var(--mu)}}dd{{margin:0}}
figure{{margin:16px 0;background:var(--pn);padding:12px;border-radius:10px}}figure img{{width:100%;max-width:822px;border-radius:4px}}figcaption{{color:var(--mu);font-size:14px;margin-top:6px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}}th,td{{border-bottom:1px solid var(--ln);padding:6px;text-align:left;vertical-align:top}}th{{color:var(--mu)}}tr.xx td{{color:#ff9b91}}
.caps{{display:flex;gap:6px;overflow-x:auto}}.caps img{{height:300px;border-radius:4px}}.wide img{{width:100%;border-radius:4px}}
@media(max-width:640px){{dl{{grid-template-columns:1fr}}.lado b{{display:block}}.lado img{{width:100%}}.inst{{margin-left:0}}}}
</style></head><body><main>
<h1>Galeria V2 × V2.1</h1>
<p class="mu">Ramo <code>visual-v2-1-refinamento</code> (derivado de <code>visual-v2</code>), sem merge. Página privada.</p>
<div class="aviso"><b>Nada aqui é aprovação visual.</b> “Aprovado tecnicamente” = testes e medição sem defeito conhecido. A aprovação é do Heitor, olhando as capturas e prévias.</div>
<div class="kpi"><div><b>{res['composicoes']}</b>composições auditadas</div><div><b>{res['estados'].get('aprovado tecnicamente', 0)} / {res['estados'].get('parcial', 0)} / {res['estados'].get('bloqueado', 0)}</b>aprovadas tec. / parciais / bloqueadas</div>
<div><b>{sel.get('positivos_passaram')}/{sel.get('positivos_total')}</b>seleção, 8 domínios (antes {sel0.get('positivos_passaram')}/{sel0.get('positivos_total')})</div><div><b>{sel.get('reserva_passaram')}/{sel.get('reserva_total')}</b>seleção, reserva não ajustada</div>
<div><b>{fb.get('detectados')}/{fb.get('total')}</b>defeitos injetados pegos pelo fiscal ({fb.get('falsos_positivos')} falso positivo)</div><div><b>{ex.get('audio', {}).get('duracao_s')} s</b>vídeo integrado, sincronia medida</div></div>
<nav><a href="#composicoes">Composições</a><a href="#panama">Panamá V1 × V2 × V2.1</a><a href="#experimental">Pipeline experimental</a><a href="#temas">Temas</a><a href="#selecao">Seleção</a><a href="#fiscal">Fiscal</a><a href="#desempenho">Desempenho</a></nav>

<h2 id="composicoes">Composições ({res['composicoes']})</h2>
<p class="mu">Cada linha: V2 em cima, V2.1 embaixo, nos mesmos 4 instantes. Prévias em movimento nas composições que mudaram visivelmente. Mudanças globais: zonas por plataforma, legenda adaptativa por cena, texto ≥ 26 px.</p>
<div class="filtros"><button class="on" data-f="">todas</button><button data-f="aprovado tecnicamente">aprovado tecnicamente</button><button data-f="parcial">parcial</button><button data-f="bloqueado">bloqueado</button></div>
{''.join(cards)}

<h2 id="panama">Panamá: produção (V1) × V2 × V2.1</h2>
<p class="mu">Mesmos instantes do vídeo auditado. Esquerda: render de produção; meio: V2; direita: V2.1. Fiscal V2.1 desta conversão: {'sem bloqueio' if fpan.get('aprovado_tecnicamente') else 'com bloqueio'}.</p>
{pan_html}

<h2 id="experimental">Pipeline experimental — roteiro → render → fiscal</h2>
<div class="aviso">Áudio do teste: <b>{e(ex.get('audio', {}).get('tipo', ''))}</b>. Serve para medir sincronia (o instante de cada palavra é conhecido); não é teste de voz. O áudio antigo do Panamá <b>não</b> foi usado: o roteiro corrigido (82 km; leilão de US$ 5,3 mi) não corresponde a ele.</div>
<video controls playsinline preload="none" src="experimental_540.mp4" style="max-width:360px"></video>
<div class="wide"><img loading="lazy" src="img/experimental_quadros.jpg" alt="quadros do vídeo experimental"></div>
<h3 style="margin-top:16px">Sincronia medida no palco</h3><ul>{crit}<li>{"✓" if leg.get('ok') else "✗"} legenda: {leg.get('palavras')} palavras, {leg.get('fora_do_bloco')} fora do bloco ativo; {sum((leg.get('ocultas_por_regra') or {}).values())} com legenda oculta por regra (redundante com a tela)</li></ul>
<h3>Cenas e decisões</h3><table><tr><th>#</th><th>composição</th><th>tempo (s)</th><th>fala</th><th>decisão</th></tr>{cenas_ex}</table>
<h3>Fiscal do vídeo</h3><table><tr><th>categoria</th><th>código</th><th>cena</th><th>instante</th><th>problema</th><th>evidência</th><th>gravidade</th><th>solução</th></tr>{fisc}</table>
<p class="mu">Não testado: voz humana/TTS de produção, alinhamento forçado de voz real, mixagem com música e loudness de publicação.</p>

<h2 id="temas">Temas fora do Panamá</h2><p class="mu">Dados sintéticos ou aproximados, marcados como tal. O tema “mapas” mostra o voo Lisboa–Rio, a rota aproximada de Cabral e a comparação NY–SF (canal × Cabo Horn, 9.500 × 22.500 km, Wikipedia).</p>
{temas_html or '<p class="mu">(temas ainda não renderizados)</p>'}

<h2 id="selecao">Seleção visual</h2>
<p class="mu">Positivos e negativos escritos antes de rodar; reserva escrita depois das correções e rodada uma vez, sem ajuste. As falhas da reserva vão todas para o mesmo lado: acontecimento crítico parafraseado vira foto sem limitação.</p>
<table><tr><th>id</th><th>domínio / testa</th><th>fala</th><th>escolha</th><th>aceitáveis</th><th></th></tr>{linhas_sel(sel.get('positivos', []))}{linhas_sel(sel.get('negativos', []))}</table>
<h3>Reserva ({sel.get('reserva_passaram')}/{sel.get('reserva_total')})</h3><table><tr><th>id</th><th>domínio</th><th>fala</th><th>escolha</th><th>aceitáveis</th><th></th></tr>{linhas_sel(sel.get('reserva', []))}</table>

<h2 id="fiscal">Fiscal: defeitos injetados</h2>
<table><tr><th>caso</th><th>esperado</th><th>acusou no defeito</th><th>acusou no correto</th><th>evidência</th></tr>{bench}</table>

<h2 id="desempenho">Desempenho</h2>
<table><tr><th>medida</th><th>valor</th></tr>
<tr><td>captura das composições (4 instantes + medição)</td><td>V2 91,4 s (32) → V2.1 97,2 s (33); mapas 21–26 s cada (MapLibre em SwiftShader)</td></tr>
<tr><td>vídeo integrado de {ex.get('audio', {}).get('duracao_s')} s</td><td>render {ex.get('tempos', {}).get('render_s')} s; medição {ex.get('tempos', {}).get('medicao_s')} s; pico ≈ 0,5 GB; {ex.get('tamanho_video_mb')} MB</td></tr>
<tr><td>prévias (20 fps, 540 px)</td><td>{', '.join(f'{k} {v} s' for k, v in tempos_prev.items())}</td></tr>
<tr><td>testes V2 + V2.1</td><td>43 passam em 164 s; suíte inteira: 5 falhas pré-existentes, idênticas em main (prompts no cofre privado)</td></tr></table>
</main>
<script>
document.querySelectorAll('.filtros button').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.filtros button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.comp').forEach(c=>{{c.style.display=!b.dataset.f||c.dataset.estado===b.dataset.f?'':'none'}});
}}));
</script></body></html>'''
    (G / 'index.html').write_text(pagina, encoding='utf-8')
    print('ok', len(pagina))


if __name__ == '__main__':
    main()
