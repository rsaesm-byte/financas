import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8784','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def run(b,mobile):
    ctx=await b.new_context(viewport={'width':412,'height':915} if mobile else {'width':1366,'height':800},device_scale_factor=2 if mobile else 1,is_mobile=mobile,has_touch=mobile)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8784/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;save();ACT.nav('manual')"); await pg.wait_for_timeout(500)
    n='m' if mobile else 'd'
    print(n,'erro',await pg.evaluate("document.querySelector('#view').innerText.includes('Erro ao')"),'largura',await pg.evaluate("document.documentElement.scrollWidth"),'topicos',await pg.locator('.man-t').count())
    await pg.screenshot(path=f'man-{n}1.png')
    await pg.click('#man-cartoes summary'); await pg.wait_for_timeout(400); await pg.locator('#man-cartoes').scroll_into_view_if_needed(); await pg.screenshot(path=f'man-{n}2.png')
    print(' lido',await pg.evaluate("localStorage.getItem('finm_manual')"))
    await pg.fill('#manBusca','sincronizar token'); await pg.wait_for_timeout(200)
    print(' busca visiveis',await pg.evaluate("[...document.querySelectorAll('#manGrid .man-t')].filter(e=>!e.hidden).map(e=>e.id).join(',')"))
    await pg.fill('#manBusca','xyzabc'); print(' vazio',await pg.evaluate("!document.querySelector('#manVazio').hidden")); await pg.fill('#manBusca','')
    await pg.click('[data-act=manArea][data-id=sistema]'); await pg.wait_for_timeout(200); print(' area sistema',await pg.locator('.man-t').count())
    await pg.evaluate("window.scrollTo(0,0)"); await pg.click('[data-act=tour]'); await pg.wait_for_timeout(1300)
    steps=0
    while await pg.locator('#tour .tour-cx').count() and steps<12:
      t=await pg.inner_text('#tour h3'); r=await pg.evaluate("(()=>{const f=document.querySelector('.tour-furo').getBoundingClientRect(),c=document.querySelector('.tour-cx').getBoundingClientRect();return [Math.round(f.top),Math.round(f.height),Math.round(c.top),Math.round(c.bottom),c.left>=0&&c.right<=innerWidth&&c.top>=0&&c.bottom<=innerHeight]})()")
      print('  tour',steps+1,t,r)
      if steps==2: await pg.screenshot(path=f'man-{n}3.png')
      await pg.click('[data-act=tourProx]'); await pg.wait_for_timeout(450); steps+=1
    print(' tour fim',steps,'passos; overlay',await pg.locator('#tour').count())
    await pg.evaluate("ACT.nav('manual')"); await pg.wait_for_timeout(200); await pg.click('.man-passos .mrow >> nth=2'); await pg.wait_for_timeout(300); print(' passo 3 leva para',await pg.evaluate("view"))
    print(errs or ' no errors'); await ctx.close()
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    await run(b,True); await run(b,False); await b.close()
asyncio.run(main()); srv.terminate()
