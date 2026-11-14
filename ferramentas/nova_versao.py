"""Prepara uma versão nova para publicar: troca o número da versão em todos os lugares.

Uso:  python ferramentas/nova_versao.py          → 2026.11.14-6 (data de hoje + sequência)
      python ferramentas/nova_versao.py 2026.12.01-1

Atualiza: APP_VERSAO em js/app.js, os ?v= do index.html (css e js) e o cache do sw.js
(VERSAO financas-celular-vNN + 1). Sem isso o celular continuaria usando os arquivos antigos."""
import datetime, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ler = lambda p: open(os.path.join(R, p), encoding='utf-8').read()
def grava(p, s): open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
js, html, sw = ler('js/app.js'), ler('index.html'), ler('sw.js')
atual = re.search(r"APP_VERSAO='([^']+)'", js).group(1)
if len(sys.argv) > 1: nova = sys.argv[1]
else:
    hoje = datetime.date.today().strftime('%Y.%m.%d'); d, _, n = atual.partition('-')
    nova = f"{hoje}-{int(n or 0)+1 if d == hoje else 1}"
js = js.replace(f"APP_VERSAO='{atual}'", f"APP_VERSAO='{nova}'")
html = re.sub(r'(css/app\.css|js/app\.js)\?v=[\w.\-]+', lambda m: f'{m.group(1)}?v={nova}', html)
cache = int(re.search(r"financas-celular-v(\d+)", sw).group(1)) + 1
sw = re.sub(r"financas-celular-v\d+", f"financas-celular-v{cache}", sw)
sw = re.sub(r"const APP = '[^']+'", f"const APP = '{nova}'", sw)
grava('js/app.js', js); grava('index.html', html); grava('sw.js', sw)
print(f"versão {atual} → {nova} · cache financas-celular-v{cache}")
