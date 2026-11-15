import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8795','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':1600,'height':900})
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8795/'); await pg.wait_for_timeout(800)
    await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
    await pg.evaluate("document.querySelectorAll('.coach').forEach(x=>x.remove())")
    print('selo celular?', 'celular' in (await pg.inner_text('.brand')).lower(), 'título', await pg.title())
    ok=0
    for k in ['home','report','budget','expenses','cards','sairdividas','tela','dashboard']:
      await pg.evaluate('scrollTo(0,0)'); await pg.locator(f'.sidebar [data-id={k}]').scroll_into_view_if_needed(); bx=await pg.locator(f'.sidebar [data-id={k}]').bounding_box()
      await pg.mouse.move(bx['x']+40,bx['y']+bx['height']/2); await pg.mouse.down()
      await pg.evaluate("render()")   # simula a sincronização redesenhando a tela no meio do clique
      await pg.wait_for_timeout(60); await pg.mouse.up(); await pg.wait_for_timeout(250)
      v=await pg.evaluate("view"); ok+= v==k
      if v!=k: errs.append(f'clique perdido em {k} (ficou {v})')
    print('cliques certos',ok,'de 8')
    print('menu rola sozinho', await pg.evaluate("(()=>{const s=document.querySelector('.sidebar');return s.scrollHeight>s.clientHeight&&getComputedStyle(s).overflowY})()"))
    await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(300)
    print('largura início',await pg.evaluate("Math.round(document.querySelector('#view').getBoundingClientRect().width)"))
    await pg.screenshot(path='pc-inicio.png')
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
