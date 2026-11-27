import json,sys
from pathlib import Path
from src.v4.formatos.cartografia_global_e396d import prepare
def main():
    spec=json.loads(Path('benchmarks/e396d/cases.json').read_text());assert spec['publish'] is False
    case=next(c for c in spec['cases'] if c['id']==sys.argv[1])
    prepare(case,Path('qa_global_e396d'))
if __name__=='__main__':main()
