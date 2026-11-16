import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8797','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SECS=['aparencia','seguranca','dados','pessoas','orcamento','exportar','app']
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    errs=[]
    for (w,h,t) in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':w,'height':h},is_mobile=t,has_touch=t,device_scale_factor=2 if t else 1)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8797/'); await pg.wait_for_timeout(800)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();document.querySelectorAll('.coach').forEach(x=>x.remove())")
      # cadeado sem bloqueio -> aba Bloqueio somente
      await pg.click('#lkBtn'); await pg.wait_for_timeout(400)
      hs=await pg.evaluate("[...document.querySelectorAll('#view h3')].map(h=>h.textContent.trim())")
      print(w,'cadeado abre:',await pg.evaluate("[view,ui.cfg]"),hs)
      if hs!=['👁 Esconder valores','🔒 Bloqueio do app']: errs.append('bloqueio mostra outras coisas: '+str(hs))
      await pg.screenshot(path=f'cfg-seguranca-{w}.png',full_page=True)
      for s in SECS:
        await pg.click(f'.cfg-tabs [data-id={s}]'); await pg.wait_for_timeout(250)
        hs=await pg.evaluate("[...document.querySelectorAll('#view h3')].map(h=>h.textContent.trim().slice(0,30))")
        print(' ',s,hs)
        if not hs: errs.append('aba vazia '+s)
        await pg.screenshot(path=f'cfg-{s}-{w}.png',full_page=True)
      # interruptor de animações
      await pg.click('.cfg-tabs [data-id=aparencia]'); await pg.wait_for_timeout(200)
      await pg.click('[data-act=toggleFx]'); await pg.wait_for_timeout(300)
      print(' fx ligado?',await pg.evaluate("state.settings.fx"), 'chave on?',await pg.evaluate("document.querySelector('[data-act=toggleFx] .cfg-tg').classList.contains('on')"))
      # nuvem do topo -> dados ; Mais tem Configurações
      await pg.evaluate("ACT.nav('home');ACT.cfg('dados')"); print(' cfg dados',await pg.evaluate("ui.cfg"))
      if t:
        await pg.evaluate("ACT.more()"); await pg.wait_for_timeout(300); print(' Mais tem Configurações',await pg.evaluate("!!document.querySelector('.more-item[data-id=settings]')"))
        await pg.evaluate("closeModal()")
      await ctx.close()
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
