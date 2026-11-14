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
srv=subprocess.Popen([sys.executable,'-m','http.server','8785','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',(lambda r:r.fulfill(path=CHART,content_type='application/javascript')) if CHART else (lambda r:r.abort()))
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8785/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;save();ACT.nav('home')"); await pg.wait_for_timeout(300)
    print('padrao',await pg.evaluate("[document.documentElement.dataset.skin,document.documentElement.dataset.theme].join()"))
    await pg.evaluate("ACT.more()"); await pg.wait_for_timeout(300); await pg.click('.more-item[data-act=theme]'); await pg.wait_for_timeout(400); await pg.screenshot(path='sk-picker.png')
    for k in ['dolar','onix','pergaminho','aurora','oceano']:
      await pg.click(f'.skin-card[data-id={k}]'); await pg.wait_for_timeout(350)
      print(k,await pg.evaluate("[document.documentElement.dataset.skin,document.documentElement.dataset.theme,getComputedStyle(document.body).getPropertyValue('--bg').trim(),document.querySelector('meta[name=theme-color]').content,document.querySelectorAll('.skin-card.on').length].join(' ')"))
      await pg.evaluate("closeModal()"); await pg.wait_for_timeout(250); await pg.screenshot(path=f'sk-{k}.png')
      await pg.evaluate("ACT.budTab('needs')"); await pg.wait_for_timeout(300); await pg.screenshot(path=f'sk-{k}-b.png'); await pg.evaluate("ACT.nav('home');ACT.theme()"); await pg.wait_for_timeout(300)
    await pg.click('.skin-card[data-id=aurora]'); await pg.wait_for_timeout(300); await pg.reload(); await pg.wait_for_timeout(900)
    print('apos recarregar',await pg.evaluate("document.documentElement.dataset.skin"),'largura',await pg.evaluate("document.documentElement.scrollWidth"))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
W=412
ims=[Image.open(f'sk-{k}.png').resize((W,915)) for k in ['dolar','onix','pergaminho','aurora']]
o=Image.new('RGB',(W*4,915));[o.paste(i,(W*k,0)) for k,i in enumerate(ims)];o.save('sk-all.png')
ims=[Image.open(f).resize((W,915)) for f in ['sk-picker.png','sk-onix-b.png','sk-pergaminho-b.png','sk-aurora-b.png']]
o=Image.new('RGB',(W*4,915));[o.paste(i,(W*k,0)) for k,i in enumerate(ims)];o.save('sk-all2.png')
