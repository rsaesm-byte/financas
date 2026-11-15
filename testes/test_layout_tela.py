import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8794','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    errs=[]
    for (w,h,touch,esp) in [(412,915,True,True),(1366,800,False,False),(1920,1080,False,False),(760,900,False,False),(600,900,False,True),(800,1200,True,True)]:
      ctx=await b.new_context(viewport={'width':w,'height':h},is_mobile=touch,has_touch=touch)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8794/'); await pg.wait_for_timeout(700)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      mob=await pg.evaluate("isMobile()"); bnav=await pg.evaluate("getComputedStyle(document.querySelector('.bnav')).display"); side=await pg.evaluate("getComputedStyle(document.querySelector('.sidebar')).display")
      print(w,'touch' if touch else 'mouse','mob=',mob,'bnav',bnav,'sidebar',side,'OK' if mob==esp else 'ERRADO')
      if mob!=esp: errs.append(f'layout {w}')
      if w==1366:
        await pg.screenshot(path='tela-1366.png')
        await pg.evaluate("ACT.layout('cel')"); await pg.wait_for_timeout(300)
        print(' forçado cel',await pg.evaluate("isMobile()"),await pg.evaluate("getComputedStyle(document.querySelector('.bnav')).display"))
        await pg.reload(); await pg.wait_for_timeout(700); print(' após recarregar',await pg.evaluate("isMobile()"))
        await pg.evaluate("ACT.layout('auto')"); await pg.wait_for_timeout(200); print(' auto',await pg.evaluate("isMobile()"))
        await pg.set_viewport_size({'width':500,'height':800}); await pg.wait_for_timeout(500); print(' janela 500 ->',await pg.evaluate("isMobile()"))
      if w==412:
        await pg.evaluate("ACT.layout('pc')"); await pg.wait_for_timeout(300); print(' forçado pc',await pg.evaluate("isMobile()"))
        await pg.evaluate("ACT.nav('tela')"); await pg.wait_for_timeout(300)
        await pg.screenshot(path='tela-412.png')
      await ctx.close()
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
