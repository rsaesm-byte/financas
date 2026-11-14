import asyncio, subprocess, sys
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8781','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8781/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.evaluate("state.settings.fx=false;ACT.nav('home')"); await pg.wait_for_timeout(300)
    await pg.locator('.card.money').screenshot(path='hm.png')
    n=await pg.evaluate("state.cards.length")
    await pg.click('.money [data-act=editCard] >> nth=0'); await pg.wait_for_timeout(300); await pg.fill('[name=limite]','8000'); await pg.fill('[name=nome]','Nubank Gold')
    await pg.evaluate("document.querySelector('#modalForm .body').scrollTop=9999"); await pg.screenshot(path='hm-edit.png')
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    print('editado',await pg.evaluate("JSON.stringify([state.cards[0].nome,state.cards[0].limite])"))
    await pg.click('.money [data-act=editCard] >> nth=1'); await pg.wait_for_timeout(300); await pg.click('[data-act=mDelCard]'); await pg.wait_for_timeout(400)
    await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(400)
    print('cartoes',n,'->',await pg.evaluate("state.cards.length"))
    # bloqueio com digital automática
    cdp=await ctx.new_cdp_session(pg); await cdp.send('WebAuthn.enable'); r=await cdp.send('WebAuthn.addVirtualAuthenticator',{'options':{'protocol':'ctap2','transport':'internal','hasResidentKey':True,'hasUserVerification':True,'isUserVerified':True,'automaticPresenceSimulation':True}})
    await pg.evaluate("ACT.nav('settings')"); await pg.click('[data-act=lkDefinir][data-id=senha]'); await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(200); await pg.fill('#lkSenha','1234'); await pg.press('#lkSenha','Enter'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=lkBioToggle]'); await pg.wait_for_timeout(1500)
    await pg.reload(); await pg.wait_for_timeout(2500); print('abriu sozinho com a digital ao iniciar',not await pg.evaluate("!!document.querySelector('#lock')"))
    await pg.evaluate("Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(600)
    print('fora: travado',await pg.evaluate("!!document.querySelector('#lock')"))
    await pg.evaluate("Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(2000)
    print('voltou: digital destravou',not await pg.evaluate("!!document.querySelector('#lock')"))
    # digital falha -> cai na senha
    await cdp.send('WebAuthn.setUserVerified',{'authenticatorId':r['authenticatorId'],'isUserVerified':False})
    await pg.evaluate("ACT.lkAgora()"); await pg.wait_for_timeout(2500)
    print('digital falhou -> pede senha:',await pg.evaluate("!!document.querySelector('#lock')"),'|',await pg.inner_text('#lkMsg'),'| foco',await pg.evaluate("document.activeElement.id"))
    await pg.screenshot(path='hm-lock.png')
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
