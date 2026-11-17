// Contrato dos FORMATOS (ATLAS / DOSSIÊ). Python monta, valida e faz o preflight; aqui só se desenha, de forma
// determinística (tudo é função do quadro). Posições vêm prontas em caixas (slots) calculadas no Python.
export type Caixa = { x: number; y: number; w: number; h: number };
export type Tokens = {
  cores: Record<string, string>;
  fontes: { titulo: string; dado: string };
  tempo: { entra: number; sai: number };
  palco: { mapa: { mar: string; terra: string; borda: string; agua: string; destaque: string; destaque2: string }; tecnico: { fundo: string; linha: string; grade: string }; mesa: { fundo: string; luz: string } };
};
export type PalcoKey = {
  t: number;                         // a partir deste instante (s)
  tipo: 'mapa' | 'tecnico' | 'mesa';
  camera?: { centro: [number, number]; zoom: number };
  dur_camera?: number;               // tempo da mudança de escala (s); 0 = corte
};
export type Destaque = { fonte: 'paises' | 'lagos'; nome: string; cor?: 'destaque' | 'destaque2' | 'agua'; t0: number; t1?: number };
export type Rota = { t0: number; t1: number; ate?: number; cor?: 'destaque' | 'agua'; some?: number };
export type Rotulo = { nome: string; lonlat: [number, number]; t0: number; t1?: number; estilo?: 'ponto' | 'area' | 'oceano' | 'lago' };
export type Camada = { id: string; componente: string; t0: number; t1: number; caixa: Caixa; p: any };
export type FormatoProps = {
  duracao: number;
  formato: 'atlas' | 'dossie';
  tokens: Tokens;
  geo?: { topo: any; meta?: any } | null;
  palco: PalcoKey[];
  destaques?: Destaque[];
  rotas?: Rota[];
  rotulos?: Rotulo[];
  camadas: Camada[];
  imagens?: Record<string, { src: string; w: number; h: number }>;
  furos?: { t0: number; t1: number }[];   // trechos substituídos por outro clipe (ex.: mecanismo do palco V2)
};
