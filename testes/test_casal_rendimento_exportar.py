import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8789','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    for vp in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2,is_mobile=vp[2],has_touch=vp[2],accept_downloads=True)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8789/'); await pg.wait_for_timeout(900)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();ACT.nav('settings')"); await pg.wait_for_timeout(300)
      await pg.fill('#quemNome','Rick'); await pg.click('[data-act=quemSalva]'); await pg.wait_for_timeout(200)
      await pg.evaluate("quickAdd({valor:42,tipo:'needs',cat:'Mercado',pay:'Pix'})"); await pg.wait_for_timeout(200); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      await pg.evaluate("localStorage.setItem('finm_quem','Ana');quickAdd({valor:30,tipo:'wants',cat:'Lazer',pay:state.cards.length?'card:'+state.cards[0].id:'Pix'})"); await pg.wait_for_timeout(200); await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      print('por',await pg.evaluate("[state.expenses.slice(-1)[0].por,state.cardPurchases.slice(-1)[0].por,pessoasLanc().join(',')]"))
      await pg.evaluate("document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('settings')"); await pg.wait_for_timeout(300)
      print('card',(await pg.inner_text('.card'))[-200:].replace('\n',' | '))
      await pg.screenshot(path=f'b3-set-{vp[0]}.png',full_page=False)
      # export CSV (desktop -> download)
      if not vp[2]:
        async with pg.expect_download() as dl: await pg.click('[data-act=expCSV]')
        d=await dl.value; t=open(await d.path(),encoding='utf-8-sig').read(); print('csv linhas',len(t.splitlines()),t.splitlines()[0],'|',t.splitlines()[1][:120])
      # investment
      await pg.evaluate("ACT.nav('invest')"); await pg.wait_for_timeout(200)
      await pg.evaluate("invForm()"); await pg.wait_for_timeout(200)
      await pg.fill('#modalForm [name=nome]','CDB teste'); await pg.fill('#modalForm [name=aplicado]','10000')
      await pg.select_option('#modalForm [name=rendeTipo]','cdi'); await pg.fill('#modalForm [name=taxa]','100'); await pg.wait_for_timeout(100)
      print('info',(await pg.inner_text('#rInfo'))[:90])
      await pg.screenshot(path=f'b3-inv-{vp[0]}.png',full_page=False)
      await pg.click('#modalForm [type=submit]'); await pg.wait_for_timeout(300)
      x=await pg.evaluate("JSON.stringify(state.investimentos.slice(-1)[0])"); print('inv',x[:220])
      r=await pg.evaluate("(()=>{const x=state.investimentos.slice(-1)[0];x.base.d=addM(todayYM(),-12)+todayISO().slice(7);invAtualiza();return [x.atual,taxaAnual(x),carteiraTotal()]})()")
      print('1 ano depois',r)
      await pg.evaluate("ACT.nav('manual')"); await pg.wait_for_timeout(200)
      print(vp[0],'errors',errs or 'no errors'); await ctx.close()
    await b.close()
asyncio.run(main()); srv.terminate()
