import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8773','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8773/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("ACT.nav('contas')"); await pg.wait_for_timeout(300)
    await pg.screenshot(path='ct-empty.png')
    async def add(banco,tipo,saldo,ap=''):
      await pg.evaluate("ACT.editConta()"); await pg.wait_for_timeout(200)
      await pg.fill('[name=banco]',banco); await pg.select_option('[name=tipo]',tipo); await pg.fill('[name=apelido]',ap); await pg.fill('[name=saldo]',saldo)
      await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(250)
    await add('Nubank','corrente','2350,40'); await add('Bradesco','corrente','820'); await add('Bradesco','poupanca','5000')
    await add('Itaú','corrente','310'); await add('Itaú','poupanca','1200'); await add('Santander','corrente','150')
    await add('PicPay','digital','95,30'); await add('Inter','digital','400'); await add('Mercado Pago','digital','60')
    print('contas',await pg.evaluate("state.contas.map(c=>c.nome+(c.principal?'*':'')+(c.auto?'(auto)':'')).join(' | ')"))
    # quick add pix escolhendo Bradesco corrente
    await pg.click('.bnav .fab'); await pg.wait_for_timeout(300); await pg.keyboard.type('100')
    await pg.click('#qCats .chip >> nth=0'); await pg.click('#qPays .chip:has-text("Pix")'); await pg.wait_for_timeout(100)
    vis=await pg.evaluate("!document.querySelector('#qContas').hidden"); await pg.screenshot(path='ct-quick.png')
    await pg.click('#qContas .chip:has-text("Bradesco — Conta corrente")'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    await pg.evaluate("document.querySelector('#coach')?.remove()")
    print('chips contas visiveis',vis, await pg.evaluate("JSON.stringify(state.contas.map(c=>[c.nome,Math.round(contaSaldo(c).v*100)/100]))"))
    # cartão novo com conta pagadora
    await pg.evaluate("ACT.nav('contas')"); await pg.click('[data-act=addCard]'); await pg.wait_for_timeout(200)
    await pg.fill('[name=nome]','Itaú Visa'); await pg.dispatch_event('[name=nome]','change'); await pg.fill('[name=limite]','3000'); await pg.select_option('[name=contaId]',label='Itaú — Conta corrente')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    print('card',await pg.evaluate("JSON.stringify(state.cards.at(-1))"))
    await pg.screenshot(path='ct-list.png',full_page=True)
    await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(300)
    await pg.locator('.card.money').screenshot(path='ct-home.png')
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
