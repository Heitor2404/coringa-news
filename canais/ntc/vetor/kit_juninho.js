// Juninho: jovem caipira (~20 anos) com chapéu de palha. Mesmo esqueleto/classes da Val (a classe Val anima os dois).
const JN = { camisa: '#C0453A', camisa2: '#8E2A22', jeans: '#3E5A8C', bota: '#7A4A26', cabelo: '#5A3A22', chapeu: '#E8C66A', chapeu2: '#C9A24A', fita: '#7A3A22' };
const JUNINHO_SVG = `
 <defs><pattern id="pXadJ" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="${JN.camisa}"/>
  <rect width="14" height="40" fill="${JN.camisa2}" opacity=".55"/><rect width="40" height="14" fill="${JN.camisa2}" opacity=".55"/>
  <path d="M27 0V40M0 27H40" stroke="#F2D8A0" stroke-width="2" opacity=".6"/></pattern></defs>
 <ellipse class="vsom" cx="0" cy="${VAL_PES}" rx="130" ry="20" fill="url(#gSom)"/>
 <g class="pernas">${tubo('pa1', JN.jeans, 38)}${tubo('pa2', JN.jeans, 38)}${tubo('pe1', JN.jeans, 36)}${tubo('pe2', JN.jeans, 36)}
  <ellipse class="ch1" rx="38" ry="15" fill="${JN.bota}" stroke="${L}" stroke-width="5"/><ellipse class="ch2" rx="38" ry="15" fill="${JN.bota}" stroke="${L}" stroke-width="5"/></g>
 <g class="tronco">
  <g class="bracoE">${tubo('bE1', JN.camisa, 34)}${tubo('bE2', SK, 28)}<g class="mE">${maoAberta}${maoPunho}${maoAponta}</g></g>
  <path d="M-100 -20 L-100 112 L-6 112 L0 30 L6 112 L100 112 L100 -20Z" fill="${JN.jeans}" stroke="${L}" stroke-width="6"/><path d="M-60 0 Q-40 20 -20 0 M20 0 Q40 20 60 0" stroke="#2E4670" stroke-width="4" fill="none"/>
  <path d="M-108 -40 Q-118 -230 -80 -262 Q0 -286 80 -262 Q118 -230 108 -60 L104 -14 L-104 -14Z" fill="url(#pXadJ)" stroke="${L}" stroke-width="6"/>
  <path d="M-22 -270 L0 -220 L22 -270" fill="#F2D8A0" stroke="${L}" stroke-width="5"/><path d="M0 -220 V-16" stroke="${L}" stroke-width="4" opacity=".5"/>
  ${[-170, -110, -50].map(y => `<circle cx="0" cy="${y}" r="5" fill="#F2D8A0" stroke="${L}" stroke-width="2"/>`).join('')}
  <rect x="-58" y="-180" width="40" height="34" rx="4" fill="${JN.camisa2}" stroke="${L}" stroke-width="4" opacity=".9"/>
  <rect x="-106" y="-26" width="212" height="22" rx="6" fill="#4A2E1A" stroke="${L}" stroke-width="5"/><rect x="-18" y="-28" width="36" height="26" rx="4" fill="#D9B24A" stroke="${L}" stroke-width="4"/>
  <g class="cabeca">
   <rect x="-22" y="-300" width="44" height="40" fill="${SK}" stroke="${L}" stroke-width="5"/>
   <circle cx="0" cy="-375" r="100" fill="${SK}" stroke="${L}" stroke-width="6"/>
   <path d="M-100 -390 Q-104 -440 -70 -452 L70 -452 Q104 -440 100 -390 Q90 -420 70 -424 L-70 -424 Q-90 -420 -100 -390Z" fill="${JN.cabelo}" stroke="${L}" stroke-width="5"/>
   <path d="M-100 -380 Q-110 -340 -96 -330 M100 -380 Q110 -340 96 -330" stroke="${JN.cabelo}" stroke-width="10" fill="none" stroke-linecap="round"/>
   <circle cx="-98" cy="-358" r="15" fill="${SK}" stroke="${L}" stroke-width="5"/><circle cx="98" cy="-358" r="15" fill="${SK}" stroke="${L}" stroke-width="5"/>
   <ellipse class="boch" cx="-60" cy="-328" rx="18" ry="10" fill="#E98A86" opacity=".55"/><ellipse class="boch" cx="60" cy="-328" rx="18" ry="10" fill="#E98A86" opacity=".55"/>
   ${[[-66, -340], [-54, -334], [-72, -330], [56, -340], [66, -334], [52, -330]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="2.6" fill="#B7704A"/>`).join('')}
   <path class="sbE" stroke="${L}" stroke-width="9" fill="none" stroke-linecap="round"/><path class="sbD" stroke="${L}" stroke-width="9" fill="none" stroke-linecap="round"/>
   <g class="olhos"></g>
   <path d="M-8 -352 Q0 -338 8 -352" stroke="${SK2}" stroke-width="6" fill="none"/>
   <path class="boca" fill="#7A2430" stroke="${L}" stroke-width="5" stroke-linejoin="round"/>
   <path class="lagr" d="M-40 -350 Q-46 -330 -40 -318 Q-34 -330 -40 -350Z M40 -350 Q34 -330 40 -318 Q46 -330 40 -350Z" fill="#9FD3F2" stroke="${L}" stroke-width="3" opacity="0"/>
   <path class="suor" d="M92 -430 Q104 -405 92 -398 Q80 -405 92 -430Z" fill="#9FD3F2" stroke="${L}" stroke-width="4" opacity="0"/>
   <!-- chapéu de palha -->
   <ellipse cx="0" cy="-446" rx="168" ry="30" fill="${JN.chapeu}" stroke="${L}" stroke-width="6"/>
   <path d="M-150 -446 Q0 -420 150 -446" stroke="${JN.chapeu2}" stroke-width="5" fill="none"/>
   <path d="M-82 -450 Q-88 -536 0 -540 Q88 -536 82 -450 Q0 -432 -82 -450Z" fill="${JN.chapeu}" stroke="${L}" stroke-width="6"/>
   <path d="M-84 -470 Q0 -452 84 -470 L82 -450 Q0 -432 -82 -450Z" fill="${JN.fita}" stroke="${L}" stroke-width="4"/>
   ${[-60, -30, 0, 30, 60].map(x => `<path d="M${x} -530 L${x * 1.05} -476" stroke="${JN.chapeu2}" stroke-width="3" opacity=".7"/>`).join('')}
   ${[-140, -100, 100, 140].map(x => `<path d="M${x} -440 l-6 14 M${x + 8} -438 l2 15" stroke="${JN.chapeu2}" stroke-width="3"/>`).join('')}
  </g>
  <g class="bracoD">${tubo('bD1', JN.camisa, 34)}${tubo('bD2', SK, 28)}<g class="mD">${maoAberta}${maoPunho}${maoAponta}</g></g>
 </g>`;
const PERSONAGEM_SVG = { val: () => VAL_SVG, juninho: () => JUNINHO_SVG };
