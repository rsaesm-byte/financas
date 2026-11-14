import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8780','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8780/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;ACT.nav('expenses')"); await pg.wait_for_timeout(300)
    q="(()=>{const c=state.cards[0];return [c.nome,c.limite,Math.round(cardUsed(c.id,todayYM())*100)/100,state.cardPurchases.length,state.expenses.length]})()"
    print('antes',await pg.evaluate(q))
    await pg.evaluate("expenseForm()"); await pg.wait_for_timeout(300)
    await pg.fill('[name=desc]','Tênis'); await pg.fill('[name=valor]','600'); await pg.fill('[name=cat]','Compras'); await pg.select_option('[name=tipo]','wants')
    print('parcelas oculto antes',await pg.evaluate("document.querySelector('[name=parcelas]').closest('label').hidden"))
    await pg.select_option('[name=pay]',label='💳 Crédito — Cartão Principal'); await pg.fill('[name=parcelas]','3'); await pg.wait_for_timeout(200)
    print('info',(await pg.inner_text('#payInfo')).replace('\n',' | '))
    await pg.evaluate("document.querySelector('#modalForm .body').scrollTop=9999"); await pg.screenshot(path='cc-form.png')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(600)
    print('depois',await pg.evaluate(q),await pg.evaluate("JSON.stringify(state.cardPurchases.at(-1))"))
    await pg.screenshot(path='cc-after.png')
    # editar gasto existente em Pix -> cartão
    await pg.evaluate("document.querySelector('#coach')?.remove();expenseForm(state.expenses.find(e=>e.pay==='Pix'&&!e.fundId&&!e.billId))"); await pg.wait_for_timeout(300)
    await pg.select_option('[name=pay]',label='💳 Crédito — Cartão Reserva'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(500)
    print('editado',await pg.evaluate(q),await pg.evaluate("state.cardPurchases.at(-1).cardId===state.cards[1].id"))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
