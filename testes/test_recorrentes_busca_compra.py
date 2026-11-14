import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8788','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    for vp in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2,is_mobile=vp[2],has_touch=vp[2])
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8788/'); await pg.wait_for_timeout(900)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();render()")
      # quick add with tag
      await pg.evaluate("quickAdd({valor:350,tipo:'wants',cat:'Lazer',pay:'Pix'})"); await pg.wait_for_timeout(200)
      await pg.fill('#modalForm [name=desc]','passagem #viagem #Ferias'); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      await pg.evaluate("document.querySelectorAll('.coach,.toast').forEach(x=>x.remove())")
      print('tag',await pg.evaluate("JSON.stringify(state.expenses.slice(-1).map(e=>[e.desc,e.tags]))"))
      # search
      await pg.evaluate("ACT.nav('busca')"); await pg.wait_for_timeout(200)
      await pg.fill('#buscaGeral','#viagem'); await pg.wait_for_timeout(500)
      print('busca #viagem',await pg.evaluate("buscaItens('#viagem').length"),'ifood?',await pg.evaluate("buscaItens('mercado').length"),'focus',await pg.evaluate("document.activeElement.id"))
      await pg.screenshot(path=f'b2-busca-{vp[0]}.png',full_page=True)
      await pg.click('[data-act=buscaAbre]'); await pg.wait_for_timeout(300)
      print('abre form tags=',await pg.evaluate("$('#modalForm [name=tags]').value"))
      await pg.fill('#modalForm [name=tags]','#viagem #praia'); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      print('tags editadas',await pg.evaluate("JSON.stringify(state.expenses.find(e=>e.desc==='passagem').tags)"))
      # posso comprar
      await pg.evaluate("document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('possocomprar')"); await pg.wait_for_timeout(200)
      await pg.fill('[data-pc=valor]','2500'); await pg.wait_for_timeout(200)
      print('veredito',(await pg.inner_text('#pcRes'))[:160].replace('\n',' | '))
      if await pg.evaluate("state.cards.length"):
        await pg.select_option('[data-pc=pay]',await pg.evaluate("'card:'+state.cards[0].id")); await pg.wait_for_timeout(200)
        await pg.fill('[data-pc=parcelas]','10'); await pg.wait_for_timeout(200)
        print('cartao',(await pg.inner_text('#pcRes'))[:200].replace('\n',' | '))
      await pg.screenshot(path=f'b2-pc-{vp[0]}.png',full_page=True)
      n0=await pg.evaluate("state.cardPurchases.length+state.expenses.length")
      await pg.click('[data-act=pcLanca]'); await pg.wait_for_timeout(400); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      print('lancou',await pg.evaluate("state.cardPurchases.length+state.expenses.length")-n0, await pg.evaluate("JSON.stringify(state.cardPurchases.slice(-1).map(p=>[p.valorTotal,p.parcelas]))"))
      # recorrentes: renda 3 meses atrás
      r=await pg.evaluate("""(()=>{const ym=addM(todayYM(),-3);const m=month(ym,true);m.income.push({id:'inc1',recId:'R1',recorrente:true,fonte:'Salário',natureza:'fixa',valor:5000,date:isoOf(ym,5)});
        state.bills.push({id:'bX',nome:'Academia',valor:99,dia:1,pay:'Pix',cat:'Saúde',tipo:'needs',ativo:true,auto:true,autoDesde:addM(todayYM(),-1)});
        const n=autoRecorrentes(),n2=autoRecorrentes();return [n,n2,[1,2,3].map(i=>(month(addM(ym,i)).income||[]).filter(x=>x.recId==='R1').length),state.expenses.filter(e=>e.billId==='bX').map(e=>e.id)]})()""")
      print('recorrentes',r)
      r=await pg.evaluate("""(()=>{const id='R1@'+todayYM();const m=month(todayYM());const i=m.income.find(x=>x.id===id);tomb(id);m.income=m.income.filter(x=>x!==i);autoRecorrentes();return m.income.some(x=>x.id===id)})()""")
      print('apagado volta?',r)
      await pg.evaluate("ACT.nav('expenses')"); await pg.wait_for_timeout(200)
      await pg.evaluate("incomeForm()"); await pg.wait_for_timeout(200); print('chk renda',await pg.evaluate("!!$('#modalForm [name=recorrente]')")); await pg.evaluate("closeModal()")
      await pg.evaluate("ACT.nav('manual')"); await pg.wait_for_timeout(200)
      print(vp[0],'errors',errs or 'no errors'); await ctx.close()
    await b.close()
asyncio.run(main()); srv.terminate()
