/* ADAPTADOR HYPERFRAMES → template do Coringa (13/11/2026).
 * Monta componentes do catálogo HyperFrames (código original, sem alteração — ver NOTICE.md) dentro de uma caixa da
 * cena e entrega o seek do timeline GSAP deles para o seek(t) do template.
 *  - o runtime do HyperFrames clona o <template> do componente; aqui fazemos o mesmo, sem o runtime;
 *  - variáveis: window.__hyperframes.getVariables() responde as variáveis DESTA montagem;
 *  - o componente procura #root e registra window.__timelines[nome]: guardamos o timeline e renomeamos o #root,
 *    para a próxima montagem (o mesmo componente pode aparecer duas vezes no vídeo);
 *  - o <script> do GSAP via CDN é removido (o GSAP vem local: gsap-3.14.2.min.js).
 * Tokens de cor e fonte do Coringa entram como variáveis CSS na caixa (o componente lê --brand, --fg, --font-display…).
 */
(function () {
  'use strict';
  const TOKENS = {
    '--bg': 'transparent', '--fg': '#ffffff', '--muted': 'rgba(255,255,255,.62)', '--surface': 'rgba(5,8,15,.82)',
    '--border': 'rgba(255,255,255,.16)', '--brand': '#FFD21F', '--accent': '#FFD21F', '--accent-2': '#FFD21F',
    '--font-display': "Mont, 'Montserrat', sans-serif", '--font-body': "Mont, 'Montserrat', sans-serif",
    '--font-mono': "JBM, 'JetBrains Mono', monospace", '--space-2': '12px', '--space-3': '20px',
  };
  let n = 0;
  function montar(host, nome, vars, opc = {}) {
    const fonte = (window.HF_SRC || {})[nome];
    if (!fonte || !window.gsap) return null;
    for (const k in TOKENS) host.style.setProperty(k, TOKENS[k]);
    for (const k in (opc.tokens || {})) host.style.setProperty(k, opc.tokens[k]);
    host.style.containerType = 'size';
    const doc = new DOMParser().parseFromString(fonte, 'text/html');
    const tpl = doc.querySelector('template');
    if (!tpl) return null;
    const frag = document.importNode(tpl.content, true);
    frag.querySelectorAll('script[src]').forEach(s => s.remove());          // GSAP da CDN: já carregado localmente
    // scripts clonados de <template> não executam ao inserir: recria cada um para rodar na ordem
    const scripts = [...frag.querySelectorAll('script')];
    scripts.forEach(s => s.remove());
    const id = ++n;
    // o CSS do componente mira "#root": vira um seletor só desta montagem (componentes diferentes não se misturam)
    frag.querySelectorAll('style').forEach(st => { st.textContent = st.textContent.replace(/#root\b/g, `[data-hf="${id}"]`); });
    window.__hyperframes = { getVariables: () => Object.assign({}, vars) };
    host.appendChild(frag);
    const raiz = host.querySelector('#root');
    if (raiz) raiz.setAttribute('data-hf', id);
    if (raiz && opc.duracao) raiz.setAttribute('data-duration', String(opc.duracao));
    const antes = window.__timelines && window.__timelines[nome];
    if (window.__timelines) delete window.__timelines[nome];
    for (const s of scripts) { const x = document.createElement('script'); x.textContent = s.textContent; host.appendChild(x); }
    const tl = window.__timelines && window.__timelines[nome];
    if (window.__timelines) { delete window.__timelines[nome]; if (antes) window.__timelines[nome] = antes; }
    if (raiz) raiz.removeAttribute('id');         // libera o #root para a próxima montagem
    if (!tl) return null;
    tl.pause();
    return { tl, seek: t => tl.seek(Math.max(0, t), false), duracao: tl.duration() };
  }
  window.HF = { montar, disponivel: nome => !!(window.HF_SRC && window.HF_SRC[nome] && window.gsap) };
})();
