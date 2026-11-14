import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8772','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',(lambda r:r.fulfill(path=CHART,content_type='application/javascript')) if CHART else (lambda r:r.abort()))
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8772/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(400)
    err=lambda: pg.evaluate("document.querySelector('#view').innerText.includes('Erro')")
    # informar saldo
    await pg.click('[data-act=editConta]'); await pg.wait_for_timeout(300)
    await pg.fill('[name=banco]','Nubank'); await pg.fill('[name=saldo]','2350,40'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    # simula: conta conferida ontem, gasto pix hoje
    await pg.click('.bnav .fab'); await pg.wait_for_timeout(300); await pg.keyboard.type('50'); await pg.click('#qCats .chip >> nth=0'); await pg.click('#qPays .chip:has-text("Pix")'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300); await pg.evaluate("document.querySelector('#coach')?.remove()")
    await pg.wait_for_timeout(300)
    print('conta',await pg.evaluate("JSON.stringify(contaSaldo(state.contas[0]))"),'home err',await err())
    await pg.locator('.card:has-text("Seu dinheiro hoje")').screenshot(path='h-money.png')
    for t in ['renda','needs','wants','savings','poupanca','invest','reserva']:
      await pg.evaluate(f"ACT.budTab('{t}')"); await pg.wait_for_timeout(500); 
      cats=await pg.evaluate("[...document.querySelectorAll('#view tbody tr:not(.group):not(.total) td:first-child')].length")
      print(t,'err',await err(),'linhas',cats)
      await pg.screenshot(path=f'b-{t}.png',full_page=True)
    await pg.evaluate("ACT.budTab('wants')"); await pg.click('[data-act=addBudgetTipo]'); await pg.wait_for_timeout(200)
    print('tipo preset',await pg.evaluate("document.querySelector('[name=tipo]').value"))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
