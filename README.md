# Minhas Finanças — versão para celular

Arquivos (mantenha todos juntos na mesma pasta):
- `index.html` — o app
- `manifest.json` + `icons/` — nome e ícone quando instalado na tela inicial
- `sw.js` — faz o app abrir sem internet (só funciona com o app hospedado em https)

## Publicar no GitHub Pages (grátis)
1. Crie um repositório no GitHub (ex.: `financas`).
2. Envie todos os arquivos desta pasta (Add file › Upload files).
3. Settings › Pages › Source: *Deploy from a branch* › branch `main` / pasta `/ (root)` › Save.
4. Em ~1 min o app fica em `https://SEU-USUARIO.github.io/financas/`.
5. No celular, abra esse endereço no Chrome › menu ⋮ › **Instalar app** (iPhone: Safari › Compartilhar › **Adicionar à Tela de Início**).

## Trazer os dados do computador
No PC: Configurações › Exportar backup → mande o .json para o celular → no app: Mais › Configurações › Importar backup.

## Ao atualizar o app
Troque `VERSAO` em `sw.js` (ex.: `financas-celular-v2`) junto com o novo `index.html`.

Obs.: os dados ficam no celular, não no GitHub. O repositório só guarda o programa.
