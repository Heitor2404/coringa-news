import type { MarcoProgresso, Interpolacao } from './TempoVisualE200';
// Contrato dos FORMATOS (ATLAS / DOSSIÊ). Python monta, valida e faz o preflight; aqui só se desenha, de forma
// determinística (tudo é função do quadro). Posições vêm prontas em caixas (slots) calculadas no Python.
export type Caixa = { x: number; y: number; w: number; h: number };
export type Tokens = {
  cores: Record<string, string>;
  fontes: { titulo: string; dado: string };
  tempo: { entra: number; sai: number };
  palco: { mapa: { mar: string; terra: string; borda: string; agua: string; destaque: string; destaque2: string }; tecnico: { fundo: string; linha: string; grade: string };
    mesa: { fundo: string; luz: string; madeira?: string; madeira_r?: number; madeira_g?: number; madeira_b?: number } };
};
export type PalcoKey = {
  t: number;                         // a partir deste instante (s)
  tipo: 'mapa' | 'tecnico' | 'mesa' | 'prova';
  camera?: { centro: [number, number]; zoom: number } | { foco: [number, number]; ancora: [number, number]; zoom: number };
  camera_curve?: 'cruise'; // opt-in continuous editorial movement
  dur_camera?: number;               // tempo da mudança de escala (s); 0 = corte
  deriva?: number;                   // zoom/s durante o beat (movimento lento e contínuo)
  veu?: string;                      // véu da composição (legibilidade sem cobrir o território)
  roi?: [number, number, number, number];   // território do beat (oeste, sul, leste, norte)
  composicao?: string;
};
export type Raster = { dataset?: string; nome: string; src: string; cantos: [number, number][]; de?: number | null; ate?: number | null; atribuicao: string; tipo: string;
  ajuste?: { saturacao?: number; contraste?: number; brilho_min?: number; brilho_max?: number } };
export type Destaque = { fonte: 'paises' | 'lagos'; nome: string; cor?: 'destaque' | 'destaque2' | 'agua'; t0: number; t1?: number };
export type Rota = { marcos_progresso?: MarcoProgresso[]; interpolacao?: Interpolacao; t0: number; t1: number; ate?: number; cor?: 'destaque' | 'agua'; some?: number };
export type Rotulo = { nome: string; lonlat: [number, number]; t0: number; t1?: number; estilo?: 'ponto' | 'area' | 'oceano' | 'lago' };
export type Camada = { id: string; componente: string; t0: number; t1: number; caixa: Caixa; p: any };
export type FormatoProps = {
  duracao: number;
  formato: 'atlas' | 'dossie';
  tokens: Tokens;
  geo?: { topo: any; meta?: any } | null;
  rasters?: Raster[];
  composicoes?: Record<string, { quadro: [number, number, number, number] | null; veu?: string }>;
  creditos?: { datasets: Record<string, string>; caixa: [number, number, number, number] };
  tecnico?: { pais?: string };
  neo_follow?: {start:number;end:number;zoom:number;ship?:boolean;from?:number;to?:number}; // illustrative route, opt-in private benchmark
  neo_global_style?: boolean;
  neo_route_overview?: boolean;
  neo_benchmark?: boolean; // private native viewport; not a production preset
  documentary_layout?: boolean;      // private native map bridge, no crop
  medir?: boolean;                   // registra no console a geometria REAL do quadro (validação sobre quadros renderizados)
  palco: PalcoKey[];
  destaques?: Destaque[];
  rotas?: Rota[];
  rotulos?: Rotulo[];
  camadas: Camada[];
  imagens?: Record<string, { src: string; w: number; h: number }>;
  furos?: { t0: number; t1: number }[];   // trechos substituídos por outro clipe (ex.: mecanismo do palco V2)
};
