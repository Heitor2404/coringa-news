"""Biblioteca do Ninguém Te Contou: cenários e objetos em SVG (traço chapado, contorno escuro). Desenhados uma vez."""
import pathlib
O='#2A1E1A'
def svg(w,h,body,defs=''): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><defs>{defs}</defs>{body}</svg>'

def predio(x,y,w,h,cor,jan='#FFE9A8'):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{cor}" stroke="{O}" stroke-width="6"/>'
    for j in range(y+30,y+h-60,90):
        for i in range(x+25,x+w-40,70): s+=f'<rect x="{i}" y="{j}" width="34" height="46" rx="4" fill="{jan}" stroke="{O}" stroke-width="4"/>'
    return s
def arvore(x,y,s=1,cor='#5E9E4A'):
    return (f'<rect x="{x-14*s}" y="{y}" width="{28*s}" height="{120*s}" fill="#7A4E2E" stroke="{O}" stroke-width="5"/>'
            f'<circle cx="{x}" cy="{y-30*s}" r="{90*s}" fill="{cor}" stroke="{O}" stroke-width="6"/>'
            f'<circle cx="{x-60*s}" cy="{y+10*s}" r="{55*s}" fill="{cor}" stroke="{O}" stroke-width="6"/>'
            f'<circle cx="{x+60*s}" cy="{y+10*s}" r="{55*s}" fill="{cor}" stroke="{O}" stroke-width="6"/>')
CEN={}
CEN['rua']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#BFE3F0"/><circle cx="880" cy="230" r="70" fill="#FFE07A" stroke="'+O+'" stroke-width="6"/>'
  +predio(-20,620,330,820,'#E8A87C')+predio(290,480,300,960,'#C97B84')+predio(570,700,280,740,'#8FB9A8')+predio(830,560,300,880,'#E4C26A')
  +'<rect y="1440" width="1080" height="160" fill="#B9B4AC" stroke="'+O+'" stroke-width="6"/><rect y="1600" width="1080" height="320" fill="#5B5E66"/>'
  +''.join(f'<rect x="{x}" y="1740" width="110" height="18" fill="#F2F0E8"/>' for x in range(20,1080,200))
  +'<rect x="860" y="1300" width="120" height="150" rx="10" fill="#4C8C5A" stroke="'+O+'" stroke-width="6"/><rect x="850" y="1285" width="140" height="26" rx="6" fill="#3D7449" stroke="'+O+'" stroke-width="6"/>')
CEN['floresta']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#CFE8C4"/><rect y="1350" width="1080" height="570" fill="#6B8E3D"/>'
  +arvore(140,900,1.3,'#4E8A3E')+arvore(520,780,1.6,'#5E9E4A')+arvore(920,920,1.3,'#3F7A36')
  +arvore(320,1180,1.0,'#6FAE55')+arvore(760,1160,1.05,'#5E9E4A')
  +'<rect y="1500" width="1080" height="420" fill="#7C5B3A"/>'
  +''.join(f'<ellipse cx="{x}" cy="{y}" rx="30" ry="14" fill="{c}" stroke="{O}" stroke-width="4" transform="rotate({r} {x} {y})"/>'
           for x,y,c,r in [(120,1540,'#C9822E',20),(260,1600,'#A85D2A',-30),(420,1560,'#D9A441',10),(600,1620,'#B5652B',40),(780,1570,'#C9822E',-15),(950,1610,'#D9A441',25),(180,1700,'#A85D2A',5),(520,1720,'#C9822E',-40),(860,1730,'#B5652B',15)])
  +'<rect x="330" y="1640" width="300" height="50" rx="24" fill="#8A5A34" stroke="'+O+'" stroke-width="6" transform="rotate(-8 480 1665)"/>')
CEN['horta']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#CDEBF5"/><circle cx="200" cy="260" r="80" fill="#FFE07A" stroke="'+O+'" stroke-width="6"/>'
  '<path d="M0 1100 Q300 980 600 1060 Q850 1120 1080 1020 L1080 1920 L0 1920 Z" fill="#8CC56A" stroke="'+O+'" stroke-width="6"/>'
  '<rect y="1380" width="1080" height="540" fill="#8A5A34"/>'
  +''.join(f'<path d="M{x} 1380 Q{x-20} 1300 {x-40} 1260 M{x} 1380 Q{x+20} 1300 {x+40} 1260 M{x} 1380 L{x} 1240" stroke="#3F8A3A" stroke-width="12" fill="none" stroke-linecap="round"/><ellipse cx="{x}" cy="1236" rx="22" ry="16" fill="#5EAE4A" stroke="{O}" stroke-width="4"/>' for x in range(90,1080,150))
  +''.join(f'<path d="M0 {y} L1080 {y}" stroke="#6E4527" stroke-width="10"/>' for y in (1500,1640,1780)))
CEN['lab']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#E4EEF2"/><rect y="0" width="1080" height="1000" fill="#D5E4EA"/>'
  '<rect x="80" y="260" width="420" height="300" rx="12" fill="#FFFFFF" stroke="'+O+'" stroke-width="8"/>'
  '<path d="M120 500 L200 420 L280 460 L360 340 L460 380" fill="none" stroke="#E07A6B" stroke-width="10" stroke-linecap="round"/>'
  '<text x="290" y="310" font-family="Inter" font-weight="900" font-size="30" text-anchor="middle" fill="'+O+'">NITROGÊNIO NO SOLO</text>'
  '<rect x="0" y="1180" width="1080" height="60" fill="#FFFFFF" stroke="'+O+'" stroke-width="8"/><rect y="1240" width="1080" height="680" fill="#9FB7C2" stroke="'+O+'" stroke-width="8"/>'
  '<path d="M640 1060 L640 980 L700 980 L700 1060 L740 1180 L600 1180 Z" fill="#BDE7C6" stroke="'+O+'" stroke-width="6"/>'
  '<rect x="800" y="960" width="60" height="220" rx="10" fill="#F2C14E" stroke="'+O+'" stroke-width="6"/>'
  '<circle cx="900" cy="520" r="120" fill="#FFFFFF" stroke="'+O+'" stroke-width="8"/><circle cx="900" cy="520" r="90" fill="#C9E4D0"/>'
  '<text x="900" y="535" font-family="Inter" font-weight="900" font-size="34" text-anchor="middle" fill="'+O+'">SOLO</text>')
PROP={}
PROP['barata']=svg(160,110,
  f'<g stroke="{O}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M40 40 L10 20 M40 70 L8 90 M80 34 L70 6 M80 76 L70 104 M115 42 L140 20 M115 68 L140 92"/><path d="M128 50 Q155 30 158 8 M128 60 Q156 70 158 96"/></g>'
  f'<ellipse cx="80" cy="55" rx="58" ry="32" fill="#7A3E1E" stroke="{O}" stroke-width="6"/><path d="M80 25 L80 85" stroke="{O}" stroke-width="4"/>'
  f'<ellipse cx="128" cy="55" rx="18" ry="16" fill="#5A2C14" stroke="{O}" stroke-width="6"/><ellipse cx="62" cy="44" rx="16" ry="8" fill="#B5683A" opacity=".7"/>')
PROP['rato']=svg(260,170,
  f'<path d="M30 120 Q-10 100 10 60" fill="none" stroke="{O}" stroke-width="8" stroke-linecap="round"/>'
  f'<ellipse cx="120" cy="110" rx="90" ry="50" fill="#9A9A9A" stroke="{O}" stroke-width="6"/><circle cx="200" cy="90" r="40" fill="#A9A9A9" stroke="{O}" stroke-width="6"/>'
  f'<circle cx="190" cy="52" r="22" fill="#E8A9B0" stroke="{O}" stroke-width="5"/><circle cx="214" cy="84" r="6" fill="{O}"/><circle cx="240" cy="98" r="8" fill="#E07A8B" stroke="{O}" stroke-width="4"/>'
  f'<path d="M232 104 L258 100 M232 108 L258 116" stroke="{O}" stroke-width="3"/>')
PROP['passaro']=svg(220,180,
  f'<ellipse cx="100" cy="100" rx="70" ry="52" fill="#4E7FC2" stroke="{O}" stroke-width="6"/><circle cx="160" cy="62" r="36" fill="#5B8FD6" stroke="{O}" stroke-width="6"/>'
  f'<path d="M190 60 L222 70 L190 80 Z" fill="#F2C14E" stroke="{O}" stroke-width="5"/><circle cx="168" cy="54" r="7" fill="{O}"/>'
  f'<path d="M70 90 Q110 60 130 110 Z" fill="#3B6AA8" stroke="{O}" stroke-width="5"/><path d="M90 150 L84 176 M120 150 L126 176" stroke="{O}" stroke-width="6"/>')
PROP['lixo']=svg(200,220,f'<path d="M30 60 Q100 20 170 60 Q200 200 100 210 Q0 200 30 60 Z" fill="#3A3F4A" stroke="{O}" stroke-width="8"/><path d="M80 40 L100 10 L120 40" fill="none" stroke="{O}" stroke-width="8"/>')
PROP['folhas']=svg(400,180,''.join(f'<ellipse cx="{x}" cy="{y}" rx="44" ry="20" fill="{c}" stroke="{O}" stroke-width="5" transform="rotate({r} {x} {y})"/>'
  for x,y,c,r in [(60,140,'#C9822E',20),(140,120,'#A85D2A',-30),(220,140,'#D9A441',10),(300,120,'#B5652B',40),(350,150,'#C9822E',-15),(110,80,'#D9A441',25),(200,70,'#A85D2A',5),(280,80,'#C9822E',-40),(180,30,'#B5652B',15)]))
PROP['chinelo']=svg(140,70,f'<ellipse cx="70" cy="40" rx="64" ry="26" fill="#F2C14E" stroke="{O}" stroke-width="6"/><path d="M50 40 Q70 10 90 40" fill="none" stroke="#E07A6B" stroke-width="8"/>')
PROP['murcha']=svg(160,220,f'<path d="M80 220 Q80 130 40 90" fill="none" stroke="#8A7A3A" stroke-width="10"/><ellipse cx="34" cy="96" rx="28" ry="14" fill="#B8A44A" stroke="{O}" stroke-width="4" transform="rotate(60 34 96)"/><path d="M80 170 Q120 150 130 180" fill="none" stroke="#8A7A3A" stroke-width="8"/>')
PROP['globo']=svg(300,300,f'<circle cx="150" cy="150" r="140" fill="#7EC3E6" stroke="{O}" stroke-width="8"/><path d="M60 100 Q100 60 150 90 Q170 140 120 160 Q80 170 60 100 Z M180 170 Q230 150 250 190 Q230 250 190 240 Q170 210 180 170 Z M150 40 Q190 30 210 60 Q190 80 160 70 Z" fill="#7CBF5A" stroke="{O}" stroke-width="5"/>')
# ── mais cenários (11/11) ──
CEN['sala']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#F2E3C6"/><rect y="0" width="1080" height="1300" fill="#E9CFA3"/>'
  +''.join(f'<rect x="{x}" y="0" width="40" height="1300" fill="#E2C391"/>' for x in range(40,1080,120))
  +'<rect x="620" y="300" width="340" height="260" rx="10" fill="#9FD3E8" stroke="'+O+'" stroke-width="8"/><path d="M790 300 L790 560" stroke="'+O+'" stroke-width="8"/>'
  +'<rect x="90" y="330" width="300" height="200" rx="8" fill="#2A2E38" stroke="'+O+'" stroke-width="8"/><rect x="110" y="350" width="260" height="160" fill="#4D7FA8"/><rect x="200" y="530" width="80" height="40" fill="#555" stroke="'+O+'" stroke-width="6"/>'
  +'<rect y="1300" width="1080" height="620" fill="#B07A4A"/>'
  +''.join(f'<path d="M0 {y} L1080 {y}" stroke="#94643B" stroke-width="6"/>' for y in range(1360,1920,80))
  +'<rect x="560" y="1000" width="480" height="300" rx="40" fill="#5D8AA8" stroke="'+O+'" stroke-width="8"/><rect x="580" y="900" width="440" height="160" rx="40" fill="#6E9BB8" stroke="'+O+'" stroke-width="8"/>')
CEN['mercado']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#F4F4EE"/><rect y="0" width="1080" height="200" fill="#E85D4A"/>'
  '<text x="540" y="130" font-family="Inter" font-weight="900" font-size="80" text-anchor="middle" fill="#fff">MERCADO</text>'
  +''.join(f'<rect x="{x}" y="420" width="300" height="900" fill="#D8D2C6" stroke="{O}" stroke-width="6"/>'
           +''.join(f'<rect x="{x}" y="{y}" width="300" height="14" fill="#8A8A8A"/>'+''.join(f'<rect x="{x+12+i*48}" y="{y-80}" width="40" height="80" rx="6" fill="{c}" stroke="{O}" stroke-width="4"/>' for i,c in enumerate(['#F2C14E','#E07A6B','#5E9E4A','#4E7FC2','#F28AA8','#C9822E']))
                    for y in (600,800,1000,1200)) for x in (40,390,740))
  +'<rect y="1320" width="1080" height="600" fill="#DCDCD2"/>'+''.join(f'<path d="M{x} 1320 L{x} 1920" stroke="#C8C8BE" stroke-width="6"/>' for x in range(0,1080,180)))
CEN['praia']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#9FDCF2"/><circle cx="820" cy="300" r="90" fill="#FFE07A" stroke="'+O+'" stroke-width="6"/>'
  '<rect y="900" width="1080" height="420" fill="#3E9ECF"/><path d="M0 960 Q90 930 180 960 T360 960 T540 960 T720 960 T900 960 T1080 960" fill="none" stroke="#fff" stroke-width="8"/>'
  '<path d="M0 1240 Q270 1180 540 1240 T1080 1240 L1080 1920 L0 1920 Z" fill="#F2D59A" stroke="'+O+'" stroke-width="6"/>'
  '<path d="M140 1500 L180 1100" stroke="#8A5A34" stroke-width="22"/><path d="M180 1100 Q100 1060 40 1110 M180 1100 Q260 1050 320 1110 M180 1100 Q170 1020 120 990 M180 1100 Q230 1030 280 1010" stroke="#4E8A3E" stroke-width="26" fill="none" stroke-linecap="round"/>')
CEN['hospital']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#EAF4F4"/><rect y="0" width="1080" height="1300" fill="#D6EBEA"/>'
  '<rect x="100" y="300" width="260" height="260" rx="20" fill="#fff" stroke="'+O+'" stroke-width="8"/><path d="M230 350 L230 510 M150 430 L310 430" stroke="#E85D4A" stroke-width="40"/>'
  '<rect x="560" y="960" width="460" height="120" rx="20" fill="#fff" stroke="'+O+'" stroke-width="8"/><rect x="560" y="1080" width="460" height="40" fill="#9FB7C2" stroke="'+O+'" stroke-width="6"/>'
  '<path d="M600 1120 L600 1300 M980 1120 L980 1300" stroke="'+O+'" stroke-width="10"/><rect x="800" y="400" width="10" height="560" fill="#9AA"/><rect x="760" y="380" width="90" height="120" rx="20" fill="#BDE7F4" stroke="'+O+'" stroke-width="6"/>'
  '<rect y="1300" width="1080" height="620" fill="#C9DCDA"/>')
CEN['espaco']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#14132B"/>'+''.join(f'<circle cx="{(i*397)%1080}" cy="{(i*613)%1920}" r="{2+(i%3)}" fill="#fff" opacity=".8"/>' for i in range(90))
  +'<circle cx="540" cy="2300" r="900" fill="#3E7CC2" stroke="'+O+'" stroke-width="10"/><path d="M200 1500 Q400 1440 520 1520 Q600 1600 500 1680 M700 1460 Q860 1420 950 1520" fill="none" stroke="#7CBF5A" stroke-width="60" stroke-linecap="round"/>'
  '<circle cx="860" cy="320" r="110" fill="#D9D6CC" stroke="'+O+'" stroke-width="8"/><circle cx="830" cy="300" r="22" fill="#BDB9AE"/><circle cx="900" cy="360" r="14" fill="#BDB9AE"/>')
CEN['fazenda']=svg(1080,1920,
  '<rect width="1080" height="1920" fill="#BFE3F0"/><circle cx="180" cy="260" r="80" fill="#FFE07A" stroke="'+O+'" stroke-width="6"/>'
  '<path d="M0 1050 Q400 940 1080 1060 L1080 1920 L0 1920 Z" fill="#9CCB6A" stroke="'+O+'" stroke-width="6"/>'
  '<rect x="600" y="700" width="380" height="380" fill="#C0392B" stroke="'+O+'" stroke-width="8"/><path d="M570 720 L790 520 L1010 720 Z" fill="#8E2A20" stroke="'+O+'" stroke-width="8"/>'
  '<rect x="720" y="880" width="140" height="200" fill="#fff" stroke="'+O+'" stroke-width="6"/><path d="M720 880 L860 1080 M860 880 L720 1080" stroke="'+O+'" stroke-width="6"/>'
  +''.join(f'<path d="M{x} 1200 L{x} 1320 M{x-60} 1240 L{x+60} 1240" stroke="#8A5A34" stroke-width="12"/>' for x in range(60,1080,140)))
PROP['mosca']=svg(90,70,f'<ellipse cx="30" cy="20" rx="22" ry="14" fill="#DDEEFF" stroke="{O}" stroke-width="4" opacity=".8"/><ellipse cx="60" cy="20" rx="22" ry="14" fill="#DDEEFF" stroke="{O}" stroke-width="4" opacity=".8"/><ellipse cx="45" cy="42" rx="22" ry="18" fill="#2F3A2F" stroke="{O}" stroke-width="4"/><circle cx="36" cy="38" r="6" fill="#B33"/><circle cx="54" cy="38" r="6" fill="#B33"/>')
PROP['dinheiro']=svg(200,110,f'<rect x="6" y="6" width="188" height="98" rx="10" fill="#7CBF5A" stroke="{O}" stroke-width="6"/><circle cx="100" cy="55" r="28" fill="#A8D98A" stroke="{O}" stroke-width="5"/><text x="100" y="68" font-family="Inter" font-weight="900" font-size="36" text-anchor="middle" fill="{O}">R$</text>')
PROP['pao']=svg(200,120,f'<path d="M10 90 Q10 20 100 20 Q190 20 190 90 Z" fill="#D9A441" stroke="{O}" stroke-width="6"/><path d="M60 40 L70 70 M100 32 L108 66 M140 40 L146 70" stroke="#A86F22" stroke-width="6"/><rect x="10" y="88" width="180" height="18" rx="8" fill="#C48E33" stroke="{O}" stroke-width="5"/>')
PROP['gota']=svg(90,130,f'<path d="M45 6 Q85 70 80 90 Q75 124 45 124 Q15 124 10 90 Q5 70 45 6 Z" fill="#6FC3E8" stroke="{O}" stroke-width="6"/>')
PROP['fogo']=svg(160,200,f'<path d="M80 196 Q10 190 16 120 Q22 70 60 40 Q56 90 80 100 Q76 50 110 8 Q120 70 144 100 Q160 190 80 196 Z" fill="#F28C28" stroke="{O}" stroke-width="6"/><path d="M80 186 Q44 180 50 140 Q60 116 76 108 Q80 140 96 146 Q112 120 112 106 Q130 170 80 186 Z" fill="#FFD23F"/>')
PROP['lagarto']=svg(260,120,f'<path d="M20 70 Q60 50 120 60 Q180 54 220 66 Q250 70 256 60" fill="none" stroke="{O}" stroke-width="30" stroke-linecap="round"/><path d="M20 70 Q60 50 120 60 Q180 54 220 66 Q250 70 256 60" fill="none" stroke="#7DBE4A" stroke-width="20" stroke-linecap="round"/><circle cx="34" cy="62" r="5" fill="{O}"/><path d="M90 66 L80 100 M150 64 L160 100" stroke="{O}" stroke-width="8" stroke-linecap="round"/>')
PROP['celular']=svg(120,220,f'<rect x="6" y="6" width="108" height="208" rx="18" fill="#2A2E38" stroke="{O}" stroke-width="6"/><rect x="16" y="24" width="88" height="160" rx="6" fill="#7EC3E6"/><circle cx="60" cy="198" r="7" fill="#555"/>')
PROP['nuvem']=svg(300,160,f'<path d="M60 140 Q10 140 14 100 Q20 64 64 70 Q70 20 130 24 Q180 20 196 64 Q250 50 270 96 Q290 140 240 140 Z" fill="#9AA0A6" stroke="{O}" stroke-width="6"/>')

if __name__=='__main__':
    import shutil
    base=pathlib.Path(__file__).parent
    (base/'cen').mkdir(exist_ok=True); (base/'prop').mkdir(exist_ok=True)
    for n,s in CEN.items(): (base/'cen'/f'{n}.svg').write_text(s)
    for n,s in PROP.items(): (base/'prop'/f'{n}.svg').write_text(s)
    shutil.copy(base/'cozinha_base.svg', base/'cen'/'cozinha.svg')
    print(len(CEN),len(PROP))

