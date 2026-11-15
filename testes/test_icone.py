import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8793','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    for vp in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2,is_mobile=vp[2],has_touch=vp[2])
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      bad=[]; pg.on('response',lambda r: bad.append(r.url) if r.status>=400 and 'localhost' in r.url else None)
      await pg.goto('http://localhost:8793/'); await pg.wait_for_timeout(900)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('settings')"); await pg.wait_for_timeout(600)
      print('opções',await pg.evaluate("document.querySelectorAll('[data-act=icone]').length"))
      el=await pg.query_selector('[data-act=icone][data-id=foguete]'); await el.scroll_into_view_if_needed(); await el.click(); await pg.wait_for_timeout(300)
      print('links',await pg.evaluate("[...document.querySelectorAll('link[rel=manifest],link[rel=icon],link[rel=apple-touch-icon]')].map(l=>l.getAttribute('href')).join(' | ')"))
      await pg.reload(); await pg.wait_for_timeout(900)
      print('após recarregar',await pg.evaluate("document.querySelector('link[rel=manifest]').getAttribute('href')"))
      m=await pg.evaluate("fetch(document.querySelector('link[rel=manifest]').href).then(r=>r.json()).then(j=>Promise.all(j.icons.map(i=>fetch(new URL(i.src,document.querySelector('link[rel=manifest]').href)).then(r=>r.status))))")
      print('ícones do manifesto',m)
      await pg.evaluate("ACT.nav('settings')"); await pg.wait_for_timeout(600)
      el=await pg.query_selector('[data-act=icone][data-id=foguete]'); await el.scroll_into_view_if_needed()
      await pg.screenshot(path=f'icone-{vp[0]}.png')
      await pg.evaluate("ACT.icone('original')"); await pg.wait_for_timeout(200)
      print('original',await pg.evaluate("document.querySelector('link[rel=manifest]').getAttribute('href')"))
      print('404',bad)
      print(vp[0],'errors',errs or 'no errors'); await ctx.close()
    await b.close()
asyncio.run(main()); srv.terminate()
