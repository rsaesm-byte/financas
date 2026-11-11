/* Service worker — Minhas Finanças (celular)
   Deixa o app abrir sem internet. Os DADOS não passam por aqui: ficam no IndexedDB/localStorage do aparelho.
   Ao publicar uma versão nova do app, troque o número de VERSAO para o celular baixar os arquivos novos. */
const VERSAO = 'financas-celular-v14';
const ARQUIVOS = [
  './', './index.html', './manifest.json',
  './icons/icon-192.png?v=7', './icons/icon-512.png?v=7', './icons/icon-maskable-512.png?v=7', './icons/apple-touch-icon.png?v=7',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSAO).then(c => Promise.all(ARQUIVOS.map(u => c.add(u).catch(() => null)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSAO).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  // páginas: tenta a rede primeiro (pega atualizações) e cai para o cache se estiver offline
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req, { cache: 'no-store' }).then(r => { const cp = r.clone(); caches.open(VERSAO).then(c => c.put('./index.html', cp)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  // demais arquivos (ícones, Chart.js): cache primeiro
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok && (req.url.startsWith(self.location.origin) || req.url.includes('cdn.jsdelivr.net'))) { const cp = r.clone(); caches.open(VERSAO).then(c => c.put(req, cp)); }
    return r;
  })));
});
