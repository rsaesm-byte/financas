import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8770','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',(lambda r:r.fulfill(path=CHART,content_type='application/javascript')) if CHART else (lambda r:r.abort()))
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('C '+m.text) if m.type in('error',) else None)
    await pg.goto('http://localhost:8770/'); await pg.wait_for_timeout(1000)
    await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
    await pg.evaluate("ACT.invTab('prog')"); await pg.wait_for_timeout(600)
    err=lambda: pg.evaluate("document.querySelector('#view').innerText.includes('Erro')")
    await pg.screenshot(path='i-prog.png',full_page=True); print('prog err',await err())
    await pg.click('[data-act=progDone][data-id=diag]'); await pg.wait_for_timeout(300)
    # cortes
    await pg.locator('[data-act=corteAdd]').first.click(); await pg.wait_for_timeout(200); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    await pg.locator('[data-act=corteAdd]').first.click(); await pg.wait_for_timeout(200); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    await pg.locator('[data-act=corteBudget]').first.click(); await pg.wait_for_timeout(200)
    await pg.click('[data-act=progDone][data-id=cortes]'); await pg.wait_for_timeout(300)
    print('cortes',await pg.evaluate("JSON.stringify(inv().prog.cortes)"))
    for st in ['mini','divida','reserva','investir','apos']:
      await pg.evaluate(f"ACT.invStep('{st}')"); await pg.wait_for_timeout(400); print(st,'err',await err())
      await pg.locator('#stepBox').screenshot(path=f'i-st-{st}.png')
    await pg.evaluate("ACT.invStep('divida')"); await pg.wait_for_timeout(300)
    await pg.fill('[data-progextra]','400'); await pg.press('[data-progextra]','Tab'); await pg.wait_for_timeout(400)
    print('divida txt', (await pg.locator('#stepBox').inner_text())[:600].replace('\n',' | '))
    for tab in ['guia','perfil','carteira','sim','seg']:
      await pg.evaluate(f"ACT.invTab('{tab}')"); await pg.wait_for_timeout(600); print(tab,'err',await err())
      await pg.screenshot(path=f'i-{tab}.png',full_page=True)
    # guia open
    await pg.evaluate("ACT.invTab('guia')"); await pg.click('[data-act=invOpen][data-id=lcilca]'); await pg.wait_for_timeout(300)
    await pg.screenshot(path='i-guia-open.png')
    # quiz
    await pg.evaluate("ACT.invTab('perfil')"); await pg.wait_for_timeout(300)
    for i in range(7): await pg.click(f'[data-act=quizResp][data-id="{i}:2"]')
    await pg.click('[data-act=quizFim]'); await pg.wait_for_timeout(500)
    print('perfil',await pg.evaluate("JSON.stringify(inv().perfil)")); await pg.screenshot(path='i-perfil2.png',full_page=True)
    # carteira add
    await pg.evaluate("ACT.invTab('carteira')"); await pg.click('[data-act=invAdd]'); await pg.wait_for_timeout(300)
    await pg.fill('[name=nome]','CDB Banco X'); await pg.select_option('[name=tipo]','cdb'); await pg.fill('[name=inst]','Banco X'); await pg.fill('[name=aplicado]','230000'); await pg.fill('[name=atual]','240000,50')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    await pg.click('[data-act=invAdd]'); await pg.wait_for_timeout(300)
    await pg.fill('[name=nome]','ETF BOVA11'); await pg.select_option('[name=tipo]','etf'); await pg.fill('[name=inst]','XP'); await pg.fill('[name=aplicado]','10000'); await pg.fill('[name=atual]','11000')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(500)
    await pg.screenshot(path='i-cart2.png',full_page=True); print('cart err',await err(), await pg.evaluate("carteiraTotal()"))
    # sim
    await pg.evaluate("ACT.invTab('sim')"); await pg.wait_for_timeout(400)
    await pg.fill('[data-sim="s.ap"]','1000'); await pg.press('[data-sim="s.ap"]','Tab'); await pg.wait_for_timeout(400)
    await pg.click('[data-act=aposSalvar]'); await pg.wait_for_timeout(300)
    print('apos',await pg.evaluate("JSON.stringify(inv().apos)"))
    await pg.screenshot(path='i-sim2.png',full_page=True)
    await pg.evaluate("ACT.invTab('prog')"); await pg.wait_for_timeout(300)
    print('etapas',await pg.evaluate("JSON.stringify(progEtapas().map(e=>[e.id,e.ok,Math.round(e.pct)]))"))
    await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(300)
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
