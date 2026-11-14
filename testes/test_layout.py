import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8779','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def draw(pg,idx):
  r=await pg.locator('#lkPad svg').bounding_box(); P=lambda i:(r['x']+((i%3)*95+45)/280*r['width'], r['y']+((i//3)*95+45)/280*r['height'])
  await pg.mouse.move(*P(idx[0])); await pg.mouse.down()
  for i in idx[1:]: await pg.mouse.move(*P(i),steps=6)
  await pg.mouse.up(); await pg.wait_for_timeout(700)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8779/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;ACT.nav('settings')"); await pg.wait_for_timeout(300)
    lock="!!document.querySelector('#lock')"
    # senha
    await pg.click('[data-act=lkDefinir][data-id=senha]'); await pg.fill('#lkSenha','abc1'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(200)
    await pg.fill('#lkSenha','abc1'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(900)
    print('config',await pg.evaluate("(()=>{const c=lkGet();return [c.tipo,c.hash.length,c.auto]})()"),'overlay',await pg.evaluate(lock))
    await pg.locator('.card:has-text("Bloqueio do app")').screenshot(path='lk-card.png')
    await pg.reload(); await pg.wait_for_timeout(900); print('abre travado',await pg.evaluate(lock)); await pg.screenshot(path='lk-senha.png')
    await pg.fill('#lkSenha','errada'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(700); print('errada -> travado',await pg.evaluate(lock), await pg.inner_text('#lkMsg'))
    await pg.fill('#lkSenha','abc1'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(900); print('certa -> abriu',not await pg.evaluate(lock))
    # sair do app
    await pg.evaluate("Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'));Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
    print('saiu -> travou',await pg.evaluate(lock)); await pg.fill('#lkSenha','abc1'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(900)
    # trocar para padrão
    await pg.evaluate("ACT.nav('settings')"); await pg.click('[data-act=lkDefinir][data-id=padrao]'); await pg.fill('#lkSenha','abc1'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(900)
    await draw(pg,[0,1,2,5,8]); await draw(pg,[0,1,2,5,8]); await pg.wait_for_timeout(600)
    print('padrao',await pg.evaluate("lkGet().tipo"),'overlay',await pg.evaluate(lock))
    await pg.evaluate("ACT.lkAgora()"); await pg.wait_for_timeout(300); await draw(pg,[0,3,6,7]); print('padrao errado -> travado',await pg.evaluate(lock))
    r=await pg.locator('#lkPad svg').bounding_box(); await pg.mouse.move(r['x']+45/280*r['width'],r['y']+45/280*r['height']); await pg.mouse.down(); await pg.mouse.move(r['x']+235/280*r['width'],r['y']+45/280*r['height'],steps=8); await pg.mouse.move(r['x']+235/280*r['width'],r['y']+200/280*r['height'],steps=8); await pg.screenshot(path='lk-padrao.png'); await pg.mouse.move(r['x']+235/280*r['width'],r['y']+235/280*r['height'],steps=4); await pg.mouse.up(); await pg.wait_for_timeout(900)
    print('padrao certo -> abriu',not await pg.evaluate(lock))
    # biometria com autenticador virtual
    cdp=await ctx.new_cdp_session(pg); await cdp.send('WebAuthn.enable'); await cdp.send('WebAuthn.addVirtualAuthenticator',{'options':{'protocol':'ctap2','transport':'internal','hasResidentKey':True,'hasUserVerification':True,'isUserVerified':True,'automaticPresenceSimulation':True}})
    await pg.evaluate("ACT.nav('settings')"); await pg.click('[data-act=lkBioToggle]'); await pg.wait_for_timeout(1500); print('bio ativada',await pg.evaluate("!!lkGet().bio"))
    await pg.evaluate("ACT.lkAgora()"); await pg.wait_for_timeout(2000); print('bio destravou',not await pg.evaluate(lock))
    # 5 erros -> pausa ; esqueci
    await pg.evaluate("(()=>{const c=lkGet();c.bio=null;lkSet(c);ACT.lkAgora()})()"); await pg.wait_for_timeout(300)
    for i in range(5): await draw(pg,[0,3,6,7])
    print('pausa',await pg.inner_text('.lk-box'))
    await pg.click('[data-act=lkEsqueci]'); await pg.click('[data-act=lkApagar]'); await pg.click('[data-act=lkApagar]'); await pg.wait_for_timeout(1500)
    print('apagou: lock',await pg.evaluate("lkGet()"),'gastos',await pg.evaluate("state.expenses.length"),'overlay',await pg.evaluate(lock))
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
