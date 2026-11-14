import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
from PIL import Image
srv=subprocess.Popen([sys.executable,'-m','http.server','8786','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
L="!!document.querySelector('#lock')"
async def run(b,w,h,mob,tag):
    ctx=await b.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('C '+m.text) if m.type=='error' and 'net::' not in m.text and 'Failed to load' not in m.text else None)
    await pg.goto('http://localhost:8786/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(1300)
    print(tag,'largura',await pg.evaluate("document.documentElement.scrollWidth"),'topbar cabe',await pg.evaluate("(()=>{const t=document.querySelector('.topbar');return t.scrollWidth<=t.clientWidth+1})()"),'cadeado',await pg.inner_text('#lkBtn'))
    await pg.click('#lkBtn'); await pg.wait_for_timeout(600); print(' sem código -> vai para',await pg.evaluate("view"))
    await pg.click('[data-act=lkDefinir][data-id=senha]'); await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(200); await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(1000)
    print(' opções',await pg.evaluate("[...document.querySelectorAll('[data-act=lkAuto]')].map(e=>e.innerText).join(' | ')"),'| cadeado',await pg.inner_text('#lkBtn'))
    await pg.evaluate("ACT.nav('home')"); await pg.wait_for_timeout(1300)
    # bloquear com animação: quadros
    await pg.click('#lkBtn'); fr=[]
    for i,t in enumerate([120,170,150,250,500]):
      await pg.wait_for_timeout(t); f=f'crt-{tag}-{i}.png'; await pg.screenshot(path=f); fr.append(f)
    print(' travou',await pg.evaluate(L),'locked attr',await pg.evaluate("document.documentElement.dataset.locked"),'inert',await pg.evaluate("document.querySelector('.app').hasAttribute('inert')"),'app visível?',await pg.evaluate("getComputedStyle(document.querySelector('.app')).visibility"))
    v=await pg.evaluate("view"); await pg.keyboard.press('Control+s'); await pg.keyboard.press('/'); print(' atalhos ignorados, view igual',v==await pg.evaluate("view"))
    await pg.fill('#lkSenha','0000'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(700); print(' erro:',await pg.inner_text('#lkMsg'))
    await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(250); await pg.screenshot(path=f'crt-{tag}-open.png'); fr.append(f'crt-{tag}-open.png')
    await pg.wait_for_timeout(450); await pg.screenshot(path=f'crt-{tag}-on.png'); fr.append(f'crt-{tag}-on.png'); await pg.wait_for_timeout(900)
    print(' destravou',not await pg.evaluate(L),'locked attr',await pg.evaluate("document.documentElement.dataset.locked"),'inert',await pg.evaluate("document.querySelector('.app').hasAttribute('inert')"),'classes',await pg.evaluate("document.documentElement.className"))
    if not mob:
      await pg.keyboard.press('Alt+l'); await pg.wait_for_timeout(900); print(' Alt+L travou',await pg.evaluate(L)); await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(1400)
    # abre trancado sem piscar
    await pg.add_init_script("window._vis=[];new MutationObserver(()=>{}).observe(document,{childList:true,subtree:true});document.addEventListener('DOMContentLoaded',()=>{window._vis.push([document.documentElement.dataset.locked,getComputedStyle(document.querySelector('.app')).visibility])})")
    await pg.reload(); await pg.wait_for_timeout(1200); print(' ao abrir: trancado',await pg.evaluate(L),'no DOMContentLoaded',await pg.evaluate("JSON.stringify(window._vis)"))
    await pg.screenshot(path=f'crt-{tag}-lock.png')
    # modo sem animação
    await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(1300)
    await pg.evaluate("state.settings.fx=false;save();render();ACT.lkBotao()"); await pg.wait_for_timeout(150); print(' sem animação trava na hora',await pg.evaluate(L))
    print(errs or ' no errors'); await ctx.close(); return fr
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    fr=await run(b,412,915,True,'m'); await run(b,360,740,True,'s'); await run(b,1366,800,False,'d'); await b.close()
    ims=[Image.open(f).resize((206,458)) for f in fr]+[Image.open('crt-m-lock.png').resize((206,458))]
    o=Image.new('RGB',(206*len(ims),458));[o.paste(i,(206*k,0)) for k,i in enumerate(ims)];o.save('crt.png')
asyncio.run(main()); srv.terminate()
