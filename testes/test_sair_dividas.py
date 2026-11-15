import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8791','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    for vp in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2,is_mobile=vp[2],has_touch=vp[2])
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8791/'); await pg.wait_for_timeout(900)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('sairdividas')"); await pg.wait_for_timeout(300)
      # nova dívida em aberto (rotativo)
      await pg.evaluate("ACT.addDebtAberta()"); await pg.wait_for_timeout(200)
      await pg.fill('#modalForm [name=nome]','Rotativo cartão'); await pg.fill('#modalForm [name=saldo]','3000'); await pg.fill('#modalForm [name=juros]','14'); await pg.fill('#modalForm [name=minimo]','450')
      await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      cap=await pg.evaluate("(()=>{const c=pdCapacidade();return {renda:Math.round(c.renda),custo:Math.round(c.custo),min:Math.round(c.minimos),sobra:Math.round(c.sobra),extra:Math.round(c.extra),n:c.L.length}})()")
      print('capacidade',cap)
      sims=await pg.evaluate("(()=>{const c=pdCapacidade();return ['minimo','avalanche','bola'].map(m=>{const r=pdSimula(c.L,c.extra,m);return [m,r.meses,Math.round(r.juros),r.nunca,r.quit.map(q=>q.n).join('>')]})})()")
      print('sims',sims)
      await pg.evaluate("document.querySelectorAll('.coach').forEach(x=>x.remove())")
      await pg.screenshot(path=f'sd-{vp[0]}.png',full_page=True)
      await pg.click('[data-act=pdMetodo][data-id=bola]'); await pg.wait_for_timeout(200)
      await pg.click('[data-act=pdSalvar]'); await pg.wait_for_timeout(300)
      print('plano',await pg.evaluate("JSON.stringify({m:state.planoDividas.metodo,fim:state.planoDividas.fim,n:state.planoDividas.serie.length})"))
      # pagar rotativo com valor do plano
      await pg.click('[data-act=pdPagar]'); await pg.wait_for_timeout(200)
      v=await pg.evaluate("$('#modalForm [name=valor]').value"); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      print('pagou',v,await pg.evaluate("JSON.stringify(state.debts.map(d=>[d.nome,d.modo||'parc',d.saldo,d.parcelasPagas,d.totalParcelas]))"))
      # amortização de contrato parcelado
      r=await pg.evaluate("(()=>{const d=state.debts.find(x=>x.modo!=='aberta');const t=d.totalParcelas,p=d.parcelasPagas;pdPagarForm(d.id,d.parcela*3);return [t,p,d.id]})()"); await pg.wait_for_timeout(200)
      await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      print('amortiza antes',r[:2],'depois',await pg.evaluate(f"(()=>{{const d=find(state.debts,'{r[2]}');return [d.totalParcelas,d.parcelasPagas]}})()"))
      # status e posso comprar
      print('status',await pg.evaluate("JSON.stringify(pdStatus(pdCapacidade()))"))
      await pg.evaluate("ACT.nav('possocomprar')"); await pg.wait_for_timeout(200); await pg.fill('[data-pc=valor]','900'); await pg.wait_for_timeout(200)
      print('pc', 'atrasa' in await pg.inner_text('#pcRes'))
      await pg.evaluate("ACT.nav('debts')"); await pg.wait_for_timeout(400)
      await pg.screenshot(path=f'sd-debts-{vp[0]}.png',full_page=True)
      for v2 in ['home','dashboard','invest','report','manual','sairdividas']:
        await pg.evaluate(f"ACT.nav('{v2}')"); await pg.wait_for_timeout(250)
      print('NaN na tela?', 'NaN' in await pg.inner_text('body'))
      # sem dívidas
      await pg.evaluate("state.debts=[];ACT.nav('sairdividas')"); await pg.wait_for_timeout(200)
      print('vazio ok', 'Cadastre suas dívidas' in await pg.inner_text('body'))
      print(vp[0],'errors',errs or 'no errors'); await ctx.close()
    await b.close()
asyncio.run(main()); srv.terminate()
