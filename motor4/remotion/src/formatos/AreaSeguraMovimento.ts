/** Área segura REAL de sujeitos móveis, independente de domínio.
 *
 * Não basta a posição final da câmera: usamos a caixa do objeto inteiro em
 * cada extremo de sua trajetória, já incluindo folgas de sombra/contorno.
 * Ações fora do quadro só podem ser intencionais; este utilitário cobre as
 * fases em que a narrativa exige que o sujeito esteja totalmente visível.
 *
 * Quando um objeto não cabe sem virar um ícone minúsculo, falha explicitamente
 * em vez de cortar pixels ou fingir que o movimento foi mostrado.
 */
export type Ponto = {x:number;y:number};
export type Retangulo = {left:number;top:number;right:number;bottom:number};
export type PlanoSeguro = {scale:number;area:Retangulo;anchors:Ponto[]};

const EPS=1e-7;
const finito=(v:number)=>Number.isFinite(v);
const retanguloValido=(r:Retangulo)=>
  [r.left,r.top,r.right,r.bottom].every(finito)&&r.left<r.right&&r.top<r.bottom;

/** Define a área de ação como um INSET do recorte real da cena.
 * Um único retângulo fica responsável pelo clipPath e pelas margens; não
 * deixar um "safe" fictício maior que a máscara SVG.
 */
export function areaInterna(
  recorte:Retangulo,margens:{left:number;top:number;right:number;bottom:number},
):Retangulo {
  if(!retanguloValido(recorte) ||
    Object.values(margens).some(v=>!finito(v)||v<0)){
    throw new Error('AREA-SEGURA-MARGEM: recorte ou folga inválidos');
  }
  const out={
    left:recorte.left+margens.left,top:recorte.top+margens.top,
    right:recorte.right-margens.right,bottom:recorte.bottom-margens.bottom,
  };
  if(!retanguloValido(out))throw new Error('AREA-SEGURA-MARGEM: não sobra palco para o sujeito');
  return out;
}

export function limitesDoAtor(
  conteudo:Retangulo, pivo:Ponto, posicao:Ponto, escala:number,
):Retangulo {
  return {
    left:posicao.x+(conteudo.left-pivo.x)*escala,
    right:posicao.x+(conteudo.right-pivo.x)*escala,
    top:posicao.y+(conteudo.top-pivo.y)*escala,
    bottom:posicao.y+(conteudo.bottom-pivo.y)*escala,
  };
}

export function integralmenteVisivel(conteudo:Retangulo, area:Retangulo):boolean {
  return conteudo.left>=area.left-EPS && conteudo.right<=area.right+EPS
    && conteudo.top>=area.top-EPS && conteudo.bottom<=area.bottom+EPS;
}

export function planejarAreaSegura(
  conteudo:Retangulo,pivo:Ponto,area:Retangulo,anchors:Ponto[],
  opcoes:{minScale?:number;maxScale?:number}={},
):PlanoSeguro {
  if(!retanguloValido(conteudo)||!retanguloValido(area)||
    !finito(pivo.x)||!finito(pivo.y)||
    !anchors.length||anchors.some(p=>!finito(p.x)||!finito(p.y))){
    throw new Error('AREA-SEGURA-DADOS: caixa, área e movimento obrigatórios');
  }
  const minScale=opcoes.minScale??.70, maxScale=opcoes.maxScale??1;
  if(!finito(minScale)||!finito(maxScale)||minScale<=0||maxScale<minScale||maxScale>1){
    throw new Error('AREA-SEGURA-ESCALA: limites de zoom inválidos');
  }
  let escala=maxScale;
  // Para cada direção do sujeito, o extremo só fica mais distante do pivô
  // quando a escala aumenta. Todos os keyframes visíveis devem caber.
  for(const a of anchors){
    if(a.x<area.left || a.x>area.right || a.y<area.top || a.y>area.bottom){
      throw new Error('AREA-SEGURA-PIVO: âncora exigida fora da área segura');
    }
    for(const [d,folga] of [
      [pivo.x-conteudo.left,a.x-area.left],
      [conteudo.right-pivo.x,area.right-a.x],
      [pivo.y-conteudo.top,a.y-area.top],
      [conteudo.bottom-pivo.y,area.bottom-a.y],
    ]){
      if(d>0) escala=Math.min(escala,folga/d);
    }
  }
  if(escala<minScale-EPS){
    throw new Error('AREA-SEGURA-INVIAVEL: sujeito não cabe sem perder legibilidade');
  }
  escala=Math.min(maxScale,Math.max(minScale,escala));
  if(anchors.some(p=>!integralmenteVisivel(limitesDoAtor(conteudo,pivo,p,escala),area))){
    throw new Error('AREA-SEGURA-FALHA: objeto ainda cortado no quadro');
  }
  return {scale:escala,area,anchors};
}

/** Ajusta SOMENTE o destino solicitado, sem reposicionar estados anteriores.
 * O compositor deve checar separadamente se o destino ainda cumpre a ação
 * narrativa (ex.: objeto saiu de fato de trás do portão).
 */
export function limitarDestinoSeguro(
  conteudo:Retangulo,pivo:Ponto,area:Retangulo,escala:number,desejado:Ponto,
):Ponto {
  if(!retanguloValido(conteudo)||!retanguloValido(area)||!finito(escala)||
     escala<=0||!finito(desejado.x)||!finito(desejado.y)){
    throw new Error('AREA-SEGURA-DESTINO: informações inválidas');
  }
  const xMin=area.left-(conteudo.left-pivo.x)*escala,
    xMax=area.right-(conteudo.right-pivo.x)*escala,
    yMin=area.top-(conteudo.top-pivo.y)*escala,
    yMax=area.bottom-(conteudo.bottom-pivo.y)*escala;
  if(xMin>xMax+EPS||yMin>yMax+EPS)throw new Error('AREA-SEGURA-DESTINO: objeto maior que área');
  const ponto={x:Math.max(xMin,Math.min(xMax,desejado.x)),
               y:Math.max(yMin,Math.min(yMax,desejado.y))};
  if(!integralmenteVisivel(limitesDoAtor(conteudo,pivo,ponto,escala),area)){
    throw new Error('AREA-SEGURA-DESTINO: perda de margem do objeto');
  }
  return ponto;
}
