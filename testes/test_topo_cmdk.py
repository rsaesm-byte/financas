import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8796','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    errs=[]
    for (w,h,t) in [(1864,1000,False),(1366,800,False),(412,915,True),(360,740,True)]:
      ctx=await b.new_context(viewport={'width':w,'height':h},is_mobile=t,has_touch=t,device_scale_factor=2 if t else 1)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('http://localhost:8796/'); await pg.wait_for_timeout(800)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("document.querySelectorAll('.coach').forEach(x=>x.remove())")
      over=await pg.evaluate("(()=>{const t=document.querySelector('.topbar');return [t.scrollWidth>t.clientWidth+1, Math.round(t.getBoundingClientRect().height)]})()")
      if over[0] or over[1]>80: errs.append(f'topo {w} {over}')
      print(w,'topo transborda/altura',over, 'botões', await pg.evaluate("['.tb-busca','.tb-ic','.tb-upd'].map(s=>{const e=document.querySelector(s);return e&&getComputedStyle(e).display!=='none'})"))
      await pg.screenshot(path=f'topo-{w}.png',clip={'x':0,'y':0,'width':w,'height':90})
      # Ctrl K
      await pg.keyboard.press('Control+k'); await pg.wait_for_timeout(200)
      print(' paleta aberta',await pg.evaluate("!!document.querySelector('#cmdk')"),'foco',await pg.evaluate("document.activeElement.id"))
      await pg.keyboard.type('cart'); await pg.wait_for_timeout(150)
      print(' itens',await pg.evaluate("[...document.querySelectorAll('.ck-it b')].slice(0,5).map(x=>x.textContent)"))
      await pg.screenshot(path=f'cmdk-{w}.png')
      await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
      print(' enter ->',await pg.evaluate("view"),'fechou',await pg.evaluate("!document.querySelector('#cmdk')"))
      await pg.keyboard.press('Control+k'); await pg.keyboard.type('mercado'); await pg.wait_for_timeout(150)
      n=await pg.evaluate("document.querySelectorAll('.ck-sep').length"); print(' lançamentos',n)
      if not n: errs.append('sem lançamentos na paleta')
      await pg.keyboard.press('Escape'); await pg.wait_for_timeout(100)
      print(' esc fecha',await pg.evaluate("!document.querySelector('#cmdk')"))
      # botão layout cicla
      if t: await ctx.close(); continue
      await pg.click('.tb-ic'); await pg.wait_for_timeout(300); m1=await pg.evaluate("[layoutModo(),isMobile()]")
      await pg.click('.tb-ic'); await pg.wait_for_timeout(300); m2=await pg.evaluate("[layoutModo(),isMobile()]")
      await pg.click('.tb-ic'); await pg.wait_for_timeout(300); m3=await pg.evaluate("[layoutModo(),isMobile()]")
      print(' layout ciclo',m1,m2,m3)
      await pg.click('.tb-busca'); await pg.wait_for_timeout(200); print(' clique busca abre',await pg.evaluate("!!document.querySelector('#cmdk')"))
      await ctx.close()
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
