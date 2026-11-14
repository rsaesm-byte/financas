"""Roda todos os testes do app (Playwright + Chromium) e mostra um resumo.

Uso:   python testes/rodar.py            (todos)
       python testes/rodar.py temas gastos   (só os que contêm essas palavras)

Requisitos: pip install playwright && python -m playwright install chromium
Opcional:   CHROME=/caminho/do/chrome  ·  CHART_JS=/caminho/chart.umd.js (para testar gráficos sem internet)
Cada teste abre o app num servidor local, usa dados de exemplo e falha se a página tiver qualquer erro de JavaScript.
Capturas de tela ficam em testes/capturas/ (não vão para o GitHub)."""
import glob, os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
filtros = sys.argv[1:]
testes = sorted(t for t in glob.glob(os.path.join(AQUI, 'test_*.py')) if not filtros or any(f in t for f in filtros))
falhas = []
for t in testes:
    nome = os.path.basename(t)[5:-3]; ini = time.time()
    try:
        r = subprocess.run([sys.executable, t], cwd=AQUI, capture_output=True, text=True, timeout=420)
        saida = r.stdout + r.stderr
        ok = r.returncode == 0 and 'no errors' in saida and 'Traceback' not in saida and 'errors [' not in saida
    except subprocess.TimeoutExpired:
        saida, ok = 'tempo esgotado', False
    print(f"{'✅' if ok else '❌'} {nome:32s} {time.time()-ini:5.1f}s", flush=True)
    if not ok:
        falhas.append(nome); print('   ' + '\n   '.join(saida.strip().splitlines()[-12:]))
print(f"\n{len(testes)-len(falhas)}/{len(testes)} passaram" + (f" — falharam: {', '.join(falhas)}" if falhas else ''))
sys.exit(1 if falhas else 0)
