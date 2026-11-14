import asyncio, subprocess, sys, json
from playwright.async_api import async_playwright
# --- configuração comum (rode pelo testes/rodar.py) ---
import os as _os
APP=_os.environ.get('APP_DIR',_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
CHROME=_os.environ.get('CHROME') or None
CHART=_os.environ.get('CHART_JS','')
_os.makedirs('capturas',exist_ok=True); _os.chdir('capturas')
# ------------------------------------------------------
srv=subprocess.Popen([sys.executable,'-m','http.server','8787','-d',APP],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
    ctx=await b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route('**/chart.umd.min.js',lambda r:r.abort())
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8787/'); await pg.wait_for_timeout(900)
    await pg.click('[data-act=wizSample]'); await pg.wait_for_timeout(300)
    await pg.evaluate("state.settings.fx=false;state.contas=[{id:'c1',nome:'Nubank',banco:'Nubank',tipo:'corrente',saldo:2000,auto:true,principal:true,data:new Date(Date.now()-40*864e5).toISOString()}];save();render()")
    ex=await pg.evaluate("(()=>{const e=state.expenses.filter(e=>e.date<=todayISO()).slice(-1)[0];return [e.date,e.valor,e.desc]})()")
    d=ex[0]; dd=d[8:10]+'/'+d[5:7]+'/'+d[0:4]
    csv="Data,Valor,Identificador,Descrição\n"+f"{dd},-{ex[1]:.2f},x1,{ex[2]}\n"+f"{dd},-45.90,x2,Compra no débito - SUPERMERCADO BOM PRECO\n"+f"{dd},-23.50,x3,Compra no débito - IFOOD *RESTAURANTE\n"+f"{dd},-23.50,x4,Compra no débito - IFOOD *LANCHE\n"+f"{dd},3500.00,x5,Transferência recebida - EMPRESA SA\n"+f"{dd},-39.90,x6,NETFLIX.COM\n"
    await pg.evaluate("ACT.nav('importar')"); await pg.wait_for_timeout(300)
    async with pg.expect_file_chooser() as fc: await pg.click('[data-act=impArquivo]')
    await (await fc.value).set_files({'name':'extrato-nubank.csv','mimeType':'text/csv','buffer':csv.encode('utf-8')}); await pg.wait_for_timeout(500)
    rows=await pg.evaluate("JSON.stringify(ui.imp.rows.map(r=>[r.desc.slice(0,25),r.v,r.compra,r.ok,r.dup,r.cat]))"); print('CSV',rows)
    await pg.screenshot(path='b1-imp.png',full_page=True)
    # troca categoria de uma linha IFOOD -> as outras acompanham
    i=await pg.evaluate("ui.imp.rows.find(r=>/IFOOD/.test(r.desc)).i"); opt=await pg.evaluate(f"[...document.querySelector('[data-impcat=\"{i}\"]').options].find(o=>/Lazer/.test(o.text)).value")
    await pg.select_option(f'[data-impcat="{i}"]',opt); await pg.wait_for_timeout(200)
    print('ifood cats',await pg.evaluate("ui.imp.rows.filter(r=>/IFOOD/.test(r.desc)).map(r=>r.cat).join(',')"))
    n0=await pg.evaluate("state.expenses.length"); await pg.click('[data-act=impOk]'); await pg.wait_for_timeout(400)
    print('importou',await pg.evaluate("state.expenses.length")-n0,'view',await pg.evaluate("view"),'regra aprendida',await pg.evaluate("JSON.stringify(state.catRules)"))
    # reimportar o mesmo arquivo -> tudo duplicado
    await pg.evaluate("ACT.nav('importar')"); 
    async with pg.expect_file_chooser() as fc: await pg.click('[data-act=impArquivo]')
    await (await fc.value).set_files({'name':'extrato-nubank.csv','mimeType':'text/csv','buffer':csv.encode('utf-8')}); await pg.wait_for_timeout(400)
    print('reimport marcadas',await pg.evaluate("ui.imp.rows.filter(r=>r.ok).length"),await pg.evaluate("ui.imp.rows.map(r=>r.dup).join('|')"))
    await pg.click('[data-act=impCancela]')
    # OFX cartão (sinais negativos = compra)
    ofx="OFXHEADER:100\nDATA:OFXSGML\n<OFX><CREDITCARDMSGSRSV1><CCSTMTTRNRS><CCSTMTRS><BANKTRANLIST>"+"".join(f"<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>{d.replace('-','')}120000[-3:BRT]<TRNAMT>-{v}<FITID>f{k}<MEMO>{m}</STMTTRN>" for k,(v,m) in enumerate([('120.00','POSTO SHELL'),('59.90','SHOPEE*LOJA'),('200.00','MERCADOLIVRE*VENDEDOR 2/3')]))+f"<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>{d.replace('-','')}<TRNAMT>800.00<FITID>fp<MEMO>Pagamento recebido</STMTTRN></BANKTRANLIST></CCSTMTRS></CCSTMTTRNRS></CREDITCARDMSGSRSV1></OFX>"
    async with pg.expect_file_chooser() as fc: await pg.click('[data-act=impArquivo]')
    await (await fc.value).set_files({'name':'fatura.ofx','mimeType':'application/x-ofx','buffer':ofx.encode('latin-1')}); await pg.wait_for_timeout(500)
    print('OFX modo',await pg.evaluate("ui.imp.modo"),'fatura',await pg.evaluate("ui.imp.fatura"),await pg.evaluate("JSON.stringify(ui.imp.rows.map(r=>[r.desc,r.v,r.compra,r.ok,r.pagto||false,r.cat]))"))
    c0=await pg.evaluate("state.cardPurchases.length"); await pg.click('[data-act=impOk]'); await pg.wait_for_timeout(300); print('compras importadas',await pg.evaluate("state.cardPurchases.length")-c0)
    # lixeira
    await pg.evaluate("ACT.nav('expenses')"); eid=await pg.evaluate("state.expenses[3].id")
    await pg.evaluate(f"ACT.delExpense('{eid}')"); await pg.wait_for_timeout(400)
    print('apagado',not await pg.evaluate(f"!!find(state.expenses,'{eid}')"),'na lixeira',await pg.evaluate(f"LIX.some(x=>x.id==='{eid}')"))
    await pg.evaluate("ACT.nav('lixeira')"); await pg.wait_for_timeout(300); await pg.screenshot(path='b1-lix.png')
    await pg.click('[data-act=lixRest] >> nth=0'); await pg.wait_for_timeout(300)
    print('restaurado',await pg.evaluate(f"!!find(state.expenses,'{eid}')"),'marca',await pg.evaluate(f"state.deleted['{eid}']"))
    print('merge respeita restauração',await pg.evaluate(f"(()=>{{const R=JSON.parse(JSON.stringify(state));R.expenses=R.expenses.filter(e=>e.id!=='{eid}');R.deleted['{eid}']=new Date(Date.now()-5000).toISOString();const M=merge3(state,R,R);return !!find(M.expenses,'{eid}')}})()"))
    # voltar no tempo
    await pg.evaluate("snapAuto(true,'teste')"); await pg.wait_for_timeout(400); n1=await pg.evaluate("state.expenses.length")
    await pg.evaluate("state.expenses.push({id:'zz',desc:'Depois',valor:10,date:todayISO(),cat:'Lazer',tipo:'wants',pay:'Pix'});const g=state.expenses[0].id;tomb(g);state.expenses=state.expenses.filter(e=>e.id!==g);window._g=g;save()")
    await pg.evaluate("ui.ver=null;ACT.nav('versoes')"); await pg.wait_for_timeout(600); await pg.screenshot(path='b1-ver.png')
    await pg.click('[data-act=verSnap] >> nth=0'); await pg.wait_for_timeout(300); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(800)
    print('voltou',await pg.evaluate("state.expenses.length")==n1,'novo sumiu',not await pg.evaluate("!!find(state.expenses,'zz')"),'apagado voltou',await pg.evaluate("!!find(state.expenses,window._g)"),'zz tombado',await pg.evaluate("isDead(state.deleted.zz)"),'snaps',await pg.evaluate("kvGet('snaps').then(s=>s.map(x=>x.nota).join('|'))"))
    # pagar fatura
    c=await pg.evaluate("state.cards[0].id"); antes=await pg.evaluate(f"[cardUsed('{c}',todayYM()),proxFatura(state.cards[0]).v,contaSaldo(state.contas[0]).v]")
    await pg.evaluate(f"ACT.nav('cards')"); await pg.wait_for_timeout(300); await pg.click(f'[data-act=pagarFatura][data-id="{c}"]'); await pg.wait_for_timeout(300)
    await pg.fill('[name=valor]','100'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    depois=await pg.evaluate(f"[cardUsed('{c}',todayYM()),proxFatura(state.cards[0]).v,contaSaldo(state.contas[0]).v]"); print('fatura antes',antes,'depois',depois)
    await pg.screenshot(path='b1-card.png',full_page=True)
    # estorno
    pid=await pg.evaluate("state.cardPurchases.find(p=>p.cardId===state.cards[0].id&&p.valorTotal>0).id"); u0=await pg.evaluate(f"cardUsed('{c}',todayYM())")
    await pg.evaluate(f"purchaseForm(find(state.cardPurchases,'{pid}'))"); await pg.wait_for_timeout(300); await pg.click('[data-act=estorno]'); await pg.wait_for_timeout(300)
    await pg.fill('[name=valor]','30'); await pg.click('#modalForm footer button[type=submit]'); await pg.wait_for_timeout(300)
    print('estorno limite',round(u0,2),'->',round(await pg.evaluate(f"cardUsed('{c}',todayYM())"),2))
    # acumula
    r=await pg.evaluate("""(()=>{const ym=todayYM(),p=addM(ym,-1);const b0=month(p).budget.find(b=>b.tipo==='wants');b0.acumula=true;const b1=month(ym).budget.find(x=>x.tipo===b0.tipo&&norm(x.cat)===norm(b0.cat));b1.acumula=true;save();
      const rp=comparison(p).find(x=>norm(x.cat)===norm(b0.cat)),rc=comparison(ym).find(x=>norm(x.cat)===norm(b0.cat));return [b0.cat,rp.plan,rp.real,b1.valor,rc.plan,rc.sobra||0]})()""")
    print('acumula',r)
    await pg.evaluate("ACT.budTab('wants')"); await pg.wait_for_timeout(400); await pg.screenshot(path='b1-bud.png',full_page=True)
    print(errs or 'no errors'); await b.close()
asyncio.run(main()); srv.terminate()
