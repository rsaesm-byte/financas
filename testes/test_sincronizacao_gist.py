import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8782','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
G={}; calls=[]
async def api(route):
  rq=route.request; u=rq.url.split('?')[0]; calls.append(rq.method+' '+u.replace('https://api.github.com',''))
  H={'access-control-allow-origin':'*','access-control-allow-headers':'*','access-control-allow-methods':'*'}
  if rq.method=='OPTIONS': return await route.fulfill(status=204,headers=H)
  if rq.headers.get('authorization')!='Bearer ghp_'+'a'*36: return await route.fulfill(status=401,headers=H,body='{}')
  if u.endswith('/gists') and rq.method=='GET': return await route.fulfill(status=200,headers=H,body=json.dumps([{'id':k,'files':{n:{} for n in v}} for k,v in G.items()]))
  if u.endswith('/gists') and rq.method=='POST': G['g1']={k:v['content'] for k,v in json.loads(rq.post_data)['files'].items()}; return await route.fulfill(status=201,headers=H,body='{"id":"g1"}')
  gid=u.split('/')[-1]
  if gid not in G: return await route.fulfill(status=404,headers=H,body='{}')
  if rq.method=='PATCH': G[gid].update({k:v['content'] for k,v in json.loads(rq.post_data)['files'].items()}); return await route.fulfill(status=200,headers=H,body='{}')
  return await route.fulfill(status=200,headers=H,body=json.dumps({'id':gid,'files':{k:{'content':v,'truncated':False} for k,v in G[gid].items()}}))
async def dev(b,sample):
  ctx=await b.new_context(viewport={'width':412,'height':915},is_mobile=True,has_touch=True)
  await ctx.route('**/chart.umd.min.js',lambda r:r.abort()); await ctx.route('https://api.github.com/**',api)
  pg=await ctx.new_page(); pg.errs=[]; pg.on('pageerror',lambda e:pg.errs.append(str(e)))
  await pg.goto('http://localhost:8782/'); await pg.wait_for_timeout(900)
  await pg.click('[data-act=wizSample]' if sample else '[data-act=wizBrowser]'); await pg.evaluate("state.settings.fx=false;save();ACT.nav('settings')"); await pg.wait_for_timeout(300)
  return pg
async def conn(pg,tok):
  await pg.fill('#syToken',tok); await pg.click('[data-act=syOn]'); await pg.wait_for_timeout(1500)
N="JSON.stringify([state.expenses.length,state.cards.length,(state.contas||[]).length,SY.st,!!SY.cfg])"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    A=await dev(b,True); B=await dev(b,False)
    await conn(A,'ghp_errado'+'x'*30); print('token errado',await A.evaluate(N))
    await conn(A,'ghp_'+'a'*36); print('A conectou',await A.evaluate(N),'gist criado',list(G.keys()))
    await A.locator('.card:has-text("Sincronização entre aparelhos")').screenshot(path='sy-on.png')
    await conn(B,'ghp_'+'a'*36); print('B conectou e recebeu',await B.evaluate(N))
    # edições dos dois lados antes de sincronizar
    await A.evaluate("state.expenses.push({id:'A1',desc:'Só no A',valor:10,date:todayISO(),cat:'Mercado',tipo:'needs',pay:'Pix'});window._e=state.expenses[0].id;state.expenses[0].desc='EDITADO NO A';save()")
    await B.evaluate("state.expenses.push({id:'B1',desc:'Só no B',valor:20,date:todayISO(),cat:'Lazer',tipo:'wants',pay:'Pix'});state.expenses[1].valor=999;const d=state.expenses[2].id;tomb(d);state.expenses=state.expenses.filter(e=>e.id!==d);save();window._del=d")
    await A.wait_for_timeout(4500); await B.wait_for_timeout(1500); await A.evaluate("syncNow(true)"); await A.wait_for_timeout(1500); await B.evaluate("syncNow(true)"); await B.wait_for_timeout(1500)
    for X in (A,B,A): await X.evaluate("syncNow(true)"); await X.wait_for_timeout(1300)
    chk="JSON.stringify([state.expenses.length,!!find(state.expenses,'A1'),!!find(state.expenses,'B1'),state.expenses[0].desc,state.expenses.find(e=>e.valor===999)?.valor||0])"
    d=await B.evaluate("window._del")
    print('A',await A.evaluate(chk),'apagado sumiu',not await A.evaluate(f"!!find(state.expenses,'{d}')"))
    print('B',await B.evaluate(chk),'apagado sumiu',not await B.evaluate(f"!!find(state.expenses,'{d}')"))
    e=await A.evaluate("window._e"); print('edição do A chegou no B:',await B.evaluate(f"find(state.expenses,'{e}').desc"))
    print('iguais', await A.evaluate("JSON.stringify(state.expenses.map(e=>e.id).sort())")==await B.evaluate("JSON.stringify(state.expenses.map(e=>e.id).sort())"))
    n=len(calls); await A.evaluate("syncNow(true)"); await A.wait_for_timeout(1000); print('sem mudanças não grava:',[c for c in calls[n:]])
    # transferência
    await A.evaluate("state.contas.push({id:'c1',nome:'Nubank',banco:'Nubank',tipo:'corrente',saldo:1000,auto:true,principal:true,data:new Date(Date.now()-864e5).toISOString()},{id:'c2',nome:'Poupança',banco:'Bradesco',tipo:'poupanca',saldo:500,auto:false,data:new Date(Date.now()-864e5).toISOString()});save();ACT.nav('contas')")
    await A.click('[data-act=transferir]'); await A.fill('[name=valor]','300'); await A.click('#modalForm footer button[type=submit]'); await A.wait_for_timeout(300)
    print('transfer',await A.evaluate("JSON.stringify(state.contas.map(c=>[c.nome,contaSaldo(c).v]))"))
    await A.screenshot(path='sy-contas.png',full_page=True)
    # notificação
    print('notif',await A.evaluate("JSON.stringify([lerNotif('Compra aprovada no credito de R$ 1.234,56 em PADARIA DO ZE as 10:32'),lerNotif('Pix enviado: R$ 45,00 para MARIA SILVA'),lerNotif('Nubank: Compra de R$ 23,90 APROVADA em IFOOD *RESTAURANTE')])"))
    await A.goto('http://localhost:8782/#n='+__import__('urllib.parse').parse.quote('Compra aprovada de R$ 23,90 em MERCADO BOM no débito')); await A.wait_for_timeout(1500)
    print('link abriu lançar com',await A.evaluate("document.querySelector('[name=valor]')?.value"),await A.evaluate("document.querySelector('[name=desc]')?.value"),'hash',await A.evaluate("location.hash"))
    await A.screenshot(path='sy-notif.png'); await A.evaluate("closeModal();ACT.nav('home')"); await A.wait_for_timeout(300)
    await A.locator('.card:has-text("Próximos 30 dias")').screenshot(path='sy-cal.png')
    print(A.errs+B.errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
