# Minhas Finanças — versão para celular

App de finanças pessoais que roda no navegador (Android, iPhone e computador) e pode ser instalado na tela inicial.
Endereço: **https://rsaesm-byte.github.io/financas/**

Os dados ficam no aparelho (IndexedDB/localStorage). Se a sincronização estiver ligada, uma cópia vai para um Gist **privado** da sua conta do GitHub. Este repositório guarda só o programa — nunca dados nem tokens.

## Arquivos
| Caminho | O que é |
|---|---|
| `index.html` | A página: estrutura da tela e o pequeno script que esconde o app quando o bloqueio está ligado |
| `css/app.css` | Todo o visual (temas, efeitos, layout de celular e computador) |
| `js/app.js` | Todo o funcionamento (lançamentos, cartões, orçamento, coach, sincronização, bloqueio, manual…) |
| `sw.js` | Service worker: faz o app abrir sem internet e controla a atualização |
| `manifest.json` + `icons/` | Nome e ícone do app instalado |
| `testes/` | Testes automáticos (`python testes/rodar.py`) |
| `ferramentas/nova_versao.py` | Troca o número da versão em todos os lugares antes de publicar |

## Publicar uma versão nova
1. Edite os arquivos.
2. Rode os testes: `python testes/rodar.py` (precisa de `pip install playwright` e `python -m playwright install chromium`).
3. Troque a versão: `python ferramentas/nova_versao.py` — atualiza `APP_VERSAO`, os `?v=` do `index.html` e o cache do `sw.js`.
   Sem esse passo o celular continua com os arquivos antigos.
4. Envie para o GitHub (commit + push). Em ~1 minuto o GitHub Pages publica.
5. No celular: **Mais › 🔄 Atualizar o app** (ou feche e abra o app).

## Primeira publicação no GitHub Pages
Settings › Pages › Source: *Deploy from a branch* › `main` / `/ (root)` › Save.

## Instalar
- **Android (Chrome/Firefox):** abra o endereço › menu ⋮ › *Instalar app* / *Adicionar à tela inicial*.
- **iPhone (Safari):** Compartilhar › *Adicionar à Tela de Início*.
- **Computador (Chrome/Edge):** ícone de instalar na barra de endereço.

## Segurança
- O token do GitHub (permissão só `gist`) fica guardado apenas no aparelho. Não mande por WhatsApp/e-mail; se vazar, apague em github.com/settings/tokens e gere outro.
- A senha/padrão do bloqueio fica só no aparelho (não vai para o backup nem para a sincronização).
