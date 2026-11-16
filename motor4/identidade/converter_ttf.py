"""woff2 → ttf (fonttools) para ferramentas que leem fontes do sistema (Manim/Pango, FFmpeg drawtext). Sem alterar o desenho.
uso: python identidade/converter_ttf.py  → identidade/ttf/*.ttf ; instale com: cp identidade/ttf/*.ttf ~/.fonts && fc-cache -f"""
from pathlib import Path
from fontTools.ttLib import TTFont
d = Path(__file__).parent
for f in sorted((d / 'fontes').glob('*.woff2')):
    t = TTFont(f); t.flavor = None
    t.save(d / 'ttf' / (f.stem + '.ttf')); print(f.stem)
