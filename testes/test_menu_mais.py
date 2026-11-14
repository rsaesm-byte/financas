import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8783','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',(lambda r:r.fulfill(path=CHART,content_type='application/javascript')) if CHART else (lambda r:r.abort()))
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('C '+m.text) if m.type=='error' and 'net::' not in m.text else None)
    await pg.goto('http://localhost:8783/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;save()"); await pg.wait_for_timeout(300)
    err=lambda: pg.evaluate("document.querySelector('#view').innerText.includes('Erro')")
    for v in ['anual','fechar','dividir']:
      await pg.evaluate(f"ACT.nav('{v}')"); await pg.wait_for_timeout(700); print(v,'err',await err(),'largura',await pg.evaluate("document.documentElement.scrollWidth")); await pg.screenshot(path=f'm-{v}.png',full_page=True)
    print('recorrentes',await pg.evaluate("JSON.stringify(recorrentes().slice(0,4).map(g=>[g.desc,g.n,Math.round(g.med)]))"))
    # fechar
    await pg.evaluate("ACT.nav('fechar')"); 
    if await pg.locator('[data-act=fecAjusta]').count(): await pg.locator('[data-act=fecAjusta]').first.click(); await pg.wait_for_timeout(200)
    if await pg.locator('[data-act=fecCopiar]').count(): await pg.click('[data-act=fecCopiar]'); await pg.wait_for_timeout(200)
    await pg.click('[data-act=fecConcluir]'); await pg.wait_for_timeout(300)
    print('fechado',await pg.evaluate("JSON.stringify(Object.keys(state.fechamentos))"),'prox budget',await pg.evaluate("month(addM(curMonth,1)).budget.length"))
    # dividir
    await pg.evaluate("ACT.nav('dividir')"); await pg.click('[data-act=splitAdd]'); await pg.fill('[name=pessoa]','Alex'); await pg.fill('[name=desc]','Pizza'); await pg.fill('[name=valor]','120'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    print('saldo',await pg.evaluate("JSON.stringify(splitSaldos())")); await pg.click('[data-act=splitAcerto]'); await pg.wait_for_timeout(200); print('apos acerto',await pg.evaluate("JSON.stringify(splitSaldos())"))
    # frase
    print('frase',await pg.evaluate("JSON.stringify([lerFrase('mercado 85 no pix'),lerFrase('gasolina 150,50 cartão'),lerFrase('almoço 32 reais no vale'),lerFrase('uber 18.9 débito')])"))
    await pg.click('.bnav .fab'); await pg.wait_for_timeout(300); await pg.fill('#qFrase','restaurante 64,90 no pix'); await pg.press('#qFrase','Enter'); await pg.wait_for_timeout(500)
    print('preencheu',await pg.evaluate("[document.querySelector('[name=valor]').value,document.querySelector('#qCats .chip.on')?.innerText,document.querySelector('#qPays .chip.on')?.innerText].join(' | ')")); await pg.screenshot(path='m-frase.png')
    await pg.evaluate("closeModal()")
    # foto
    await pg.evaluate("expenseForm(state.expenses[5])"); await pg.wait_for_timeout(400)
    async with pg.expect_file_chooser() as fc: await pg.click('[data-act=fotoTroca]')
    await (await fc.value).set_files(APP+'/icons/icon-192.png'); await pg.wait_for_timeout(1200)
    print('foto',await pg.evaluate("!!document.querySelector('#fotoBox img')"),await pg.evaluate("state.expenses[5].foto"),await pg.evaluate("kvGet('foto:'+state.expenses[5].id).then(d=>Math.round(d.length/1024)+' KB')"))
    print('pl',await pg.evaluate("JSON.stringify(state.plHist)"))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
