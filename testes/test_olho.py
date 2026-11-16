import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8798','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    errs=[]
    for (w,h,t) in [(412,915,True),(360,740,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':w,'height':h},is_mobile=t,has_touch=t,device_scale_factor=2 if t else 1)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8798/'); await pg.wait_for_timeout(800)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('home')"); await pg.wait_for_timeout(300)
      txt=await pg.inner_text('#view'); import re
      n=len(re.findall(r'R\$\s?\d',txt)); print(w,'abre oculto',await pg.evaluate("OCULTO"),'valores à mostra',n,'mascarados',txt.count('•••••'))
      if n: errs.append(f'{w}: {n} valores aparecendo com OCULTO')
      over=await pg.evaluate("(()=>{const t=document.querySelector('.topbar');return t.scrollWidth>t.clientWidth+1})()"); print(' topo transborda',over)
      if over: errs.append(f'topo {w} transborda')
      await pg.screenshot(path=f'olho-oculto-{w}.png')
      await pg.click('.tb-olho'); await pg.wait_for_timeout(300)
      txt=await pg.inner_text('#view'); print(' depois do olho: oculto',await pg.evaluate("OCULTO"),'valores',len(re.findall(r'R\$\s?\d',txt)))
      await pg.screenshot(path=f'olho-visivel-{w}.png')
      await pg.click('.card.money [data-act=olho]'); await pg.wait_for_timeout(200); print(' olho do card esconde',await pg.evaluate("OCULTO"))
      await pg.click('.card.money [data-act=olho]'); await pg.wait_for_timeout(200)
      # sair do app e voltar
      await pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(100)
      print(' ao sair volta a esconder',await pg.evaluate("OCULTO"))
      await pg.evaluate("delete document.hidden")
      # preferência
      await pg.evaluate("ACT.cfg('seguranca')"); await pg.wait_for_timeout(200); await pg.click('[data-act=olhoPref]'); await pg.wait_for_timeout(200)
      await pg.reload(); await pg.wait_for_timeout(800); print(' com preferência desligada abre oculto?',await pg.evaluate("OCULTO"))
      await pg.evaluate("ACT.cfg('seguranca')"); await pg.wait_for_timeout(200); await pg.screenshot(path=f'olho-cfg-{w}.png',full_page=True)
      await ctx.close()
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
