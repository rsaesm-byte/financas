import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8799','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
TEMAS=['bolsa','moedas','rede','cedula','crescimento','juros','dolares','reais','trocados','investindo','poupanca']
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
    errs=[]
    for (w,h,t) in [(412,915,True),(1366,800,False)]:
      ctx=await b.new_context(viewport={'width':w,'height':h},is_mobile=t,has_touch=t,device_scale_factor=2 if t else 1)
      await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
      pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.on('console',lambda m: errs.append('console: '+m.text) if ('fundo WebGL' in m.text or 'ERROR' in m.text) and 'Driver Message' not in m.text else None)
      await pg.goto('http://localhost:8799/'); await pg.wait_for_timeout(800)
      await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
      await pg.evaluate("state.settings.fx=false;save();localStorage.setItem('finm_oculto_abrir','0');OCULTO=false;document.querySelectorAll('.coach').forEach(x=>x.remove());ACT.nav('home')")
      print(w,'webgl',await pg.evaluate("glOk()"))
      for k in TEMAS:
        await pg.evaluate(f"ACT.skin('{k}')"); await pg.wait_for_timeout(700)
        r=await pg.evaluate("""(()=>{const c=document.querySelector('#fundoGL');if(!c||c.style.display==='none')return 'sem canvas';
          return [document.documentElement.dataset.gl||'FALHOU',c.width+'x'+c.height,!!GLF.raf]})()""")
        print(' ',k,r)
        if not isinstance(r,list) or r[0]!=k: errs.append(k+' '+str(r))
        await pg.screenshot(path=f'gl-{k}-{w}.png')
      # fundo parado
      await pg.evaluate("ACT.toggleFundo()"); await pg.wait_for_timeout(300); print(' fundo parado anima?',await pg.evaluate("!!GLF.raf"))
      await pg.evaluate("ACT.toggleFundo()")
      # seletor com miniaturas
      await pg.evaluate("ACT.theme()"); await pg.wait_for_timeout(500)
      n=await pg.evaluate("[...document.querySelectorAll('.skin-card[data-anim]')].filter(e=>e.style.getPropertyValue('--mini')).length")
      if n!=11: errs.append(f'miniaturas {n}')
      print(' miniaturas',await pg.evaluate("[...document.querySelectorAll('.skin-card[data-anim]')].filter(e=>e.style.getPropertyValue('--mini')).length"))
      await pg.screenshot(path=f'gl-seletor-{w}.png'); await pg.evaluate("closeModal()")
      # volta para tema clássico: canvas some
      await pg.evaluate("ACT.skin('oceano')"); await pg.wait_for_timeout(300); print(' clássico sem canvas',await pg.evaluate("!document.documentElement.dataset.gl"))
      await ctx.close()
    print('errors',errs or 'no errors')
    await b.close()
asyncio.run(main()); srv.terminate()
