import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8777','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',(lambda r:r.fulfill(path=CHART,content_type='application/javascript')) if CHART else (lambda r:r.abort()))
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8777/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(200)
    await pg.evaluate("ACT.nav('expenses')"); await pg.wait_for_timeout(1300)
    await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(230); await pg.screenshot(path='fx1.png')
    print('fx',await pg.evaluate("document.documentElement.dataset.fx"),'fx-in',await pg.evaluate("document.body.classList.contains('fx-in')"))
    await pg.wait_for_timeout(1300)
    print('fx-in depois',await pg.evaluate("document.body.classList.contains('fx-in')"),'hero txt',await pg.evaluate("document.querySelector('.hero .big').textContent"))
    await pg.click('.bnav .fab'); await pg.wait_for_timeout(160); await pg.screenshot(path='fx2.png'); await pg.wait_for_timeout(400)
    await pg.keyboard.type('45'); await pg.click('#qCats .chip >> nth=0'); await pg.click('#qPays .chip >> nth=0')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(520); await pg.screenshot(path='fx3.png')
    print('moeda',await pg.evaluate("!!document.querySelector('.fx-coin')"),'coach',await pg.evaluate("!!document.querySelector('#coach')"))
    await pg.wait_for_timeout(1200); await pg.evaluate("document.querySelector('#coach')?.remove()")
    await pg.evaluate("ACT.theme()"); await pg.wait_for_timeout(800); print('tema',await pg.evaluate("state.settings.theme"))
    for v in ['budget','invest','contas','profile','learn','vale','cards','goals','report','settings']:
      await pg.evaluate(f"ACT.nav('{v}')"); await pg.wait_for_timeout(1200)
      vis=await pg.evaluate("[...document.querySelectorAll('#view>*')].every(e=>getComputedStyle(e).opacity==='1')")
      print(v,'visivel',vis,'largura',await pg.evaluate("document.documentElement.scrollWidth"))
    await pg.evaluate("ACT.more()"); await pg.wait_for_timeout(700); await pg.click('[data-act=toggleFx]'); await pg.wait_for_timeout(300)
    print('desligado',await pg.evaluate("document.documentElement.dataset.fx"))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
