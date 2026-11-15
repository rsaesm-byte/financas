"""Gera os PNG dos 10 ícones opcionais (icons/opcoes/) a partir dos desenhos SVG em icones.py. Uso: python ferramentas/icones/gerar.py"""
import asyncio,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from icones import I,svg
from playwright.async_api import async_playwright
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','icons','opcoes'); os.makedirs(OUT,exist_ok=True)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=await b.new_page()
    for (k,n,c1,c2,arte) in I:
      for (suf,modo,px) in [('192','any',192),('512','any',512),('mask','mask',512),('apple','full',180)]:
        await pg.set_viewport_size({'width':px,'height':px})
        await pg.set_content(f'<html><body style="margin:0;background:transparent">{svg(c1,c2,arte,modo)}</body></html>')
        await pg.screenshot(path=f'{OUT}/{k}-{suf}.png',omit_background=True)
    # prévia com todos
    cells=''.join(f'<div style="text-align:center;font:14px Arial;color:#ddd"><div style="width:150px;height:150px">{svg(c1,c2,a,"any",k)}</div>{n}</div>' for (k,n,c1,c2,a) in I)
    await pg.set_viewport_size({'width':860,'height':420})
    await pg.set_content(f'<body style="margin:0;background:#11151f;display:grid;grid-template-columns:repeat(5,150px);gap:18px;padding:20px">{cells}</body>')
    await pg.screenshot(path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'previa.png'))
    await b.close()
asyncio.run(main())
