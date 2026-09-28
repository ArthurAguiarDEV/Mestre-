// Mestre: acoes dentro da pagina do YouTube (pedidas pelo assistente de voz).
(() => {
  const visivel = e => !!e && e.offsetParent !== null;
  const CARTOES = 'ytd-rich-item-renderer, ytd-video-renderer, ytd-compact-video-renderer, ytd-grid-video-renderer, ' +
                  'ytd-playlist-video-renderer, ytd-playlist-panel-video-renderer, yt-lockup-view-model, ytd-rich-grid-media';
  const texto = e => ((e && (e.getAttribute('title') || e.textContent)) || '').replace(/\s+/g, ' ').trim();

  function linkDoCanal(c) {
    const a = c && c.querySelector('a[href^="/@"], a[href*="/channel/"], a[href*="/c/"]');
    return a ? a.href : '';
  }

  function canalDoCartao(c) {
    if (!c) return '';
    const escolhido = c.querySelector('ytd-channel-name #text, ytd-channel-name a, #channel-name a, #channel-name #text');
    if (texto(escolhido)) return texto(escolhido);
    for (const a of c.querySelectorAll('a[href^="/@"], a[href*="/channel/"], a[href*="/c/"]')) {
      if (texto(a)) return texto(a);
    }
    // layout novo (yt-lockup): a primeira linha de detalhes e o canal
    const linha = c.querySelector('yt-content-metadata-view-model span, .yt-content-metadata-view-model__metadata-text, ' +
                                  '.yt-content-metadata-view-model-wiz__metadata-text');
    return texto(linha);
  }

  function tituloDoCartao(c, a) {
    const t = c && c.querySelector('#video-title, #video-title-link, h3 a, h3');
    return texto(t) || texto(a);
  }

  const acoes = {
    like() {
      const b = document.querySelector('like-button-view-model button, #segmented-like-button button, ytd-toggle-button-renderer#like-button button');
      if (!b) return 'nao_achei';
      if (b.getAttribute('aria-pressed') === 'true') return 'ja';
      b.click(); return 'ok';
    },
    inscrever() {
      const b = document.querySelector('#subscribe-button button, ytd-subscribe-button-renderer button, yt-subscribe-button-view-model button');
      if (!b) return 'nao_achei';
      const t = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
      if (t.includes('inscrito') || t.includes('subscribed')) return 'ja';
      b.click(); return 'ok';
    },
    chat(mostrar) {
      const frame = document.querySelector('ytd-live-chat-frame');
      if (!frame) return 'sem_chat';
      const aberto = !frame.hasAttribute('collapsed');
      if (aberto === mostrar) return 'ja';
      const b = frame.querySelector('#show-hide-button button') || frame.querySelector('#show-hide-button');
      if (!b) return 'nao_achei';
      b.click(); return 'ok';
    },
    // Os videos que estao na pagina, na ordem da tela: titulo, canal e link
    resultados() {
      const vistos = new Map();
      for (const a of document.querySelectorAll('a[href*="/watch?v="]')) {
        if (!visivel(a)) continue;
        let id;
        try { id = new URL(a.href).searchParams.get('v'); } catch (e) { continue; }
        if (!id) continue;
        const c = a.closest(CARTOES);
        if (c && c.closest('ytd-reel-shelf-renderer, ytd-rich-shelf-renderer[is-shorts]')) continue;
        let item = vistos.get(id);
        if (!item) { item = {titulo: '', canal: '', canal_link: '', link: 'https://www.youtube.com/watch?v=' + id}; vistos.set(id, item); }
        if (!item.titulo) item.titulo = tituloDoCartao(c, a);
        if (!item.canal) item.canal = canalDoCartao(c);
        if (!item.canal_link) item.canal_link = linkDoCanal(c);
      }
      return Array.from(vistos.values()).filter(i => i.titulo);
    },
    pular(segundos) {
      const v = document.querySelector('video');
      if (!v) return false;
      v.currentTime = Math.max(0, v.currentTime + segundos); return true;
    },
    volume(p) {
      const v = document.querySelector('video');
      if (!v) return 'sem_video';
      if (p.acao === 'mudo') v.muted = true;
      else if (p.acao === 'som') v.muted = false;
      else {
        v.muted = false;
        const alvo = p.acao === 'definir' ? p.valor : v.volume + (p.acao === 'mais' ? 1 : -1) * p.valor;
        v.volume = Math.max(0, Math.min(1, alvo));
      }
      return 'ok';
    },
    pausar() {
      const v = document.querySelector('video');
      if (!v) return 'sem_video';
      if (v.paused) return 'ja';
      v.pause(); return 'ok';
    },
    continuar() {
      const v = document.querySelector('video');
      if (!v) return 'sem_video';
      if (!v.paused) return 'ja';
      v.play(); return 'ok';
    },
    proximo() {
      const b = document.querySelector('.ytp-next-button');
      if (b && visivel(b) && b.getAttribute('aria-disabled') !== 'true') { b.click(); return 'ok'; }
      return 'nao_achei';
    },
    // O que tem na tela agora (para o Mestre saber onde voce esta)
    info() {
      const v = document.querySelector('video');
      const canal = document.querySelector('ytd-watch-metadata ytd-channel-name a, #owner ytd-channel-name a');
      return {url: location.href, titulo: document.title, assistindo: location.pathname === '/watch',
              tocando: !!v && !v.paused, canal: texto(canal), canal_link: canal ? canal.href : ''};
    },
    tela_cheia() { return !!document.fullscreenElement; },
    // Para o Mestre ajustar o leitor quando o YouTube muda o visual (vai para logs/youtube_retrato.txt)
    retrato() {
      const links = Array.from(document.querySelectorAll('a[href*="/watch?v="]'));
      const cartao = links.map(a => a.closest(CARTOES) || a.parentElement).find(Boolean);
      return {url: location.href, links_de_video: links.length, visiveis: links.filter(visivel).length,
              exemplo: cartao ? cartao.outerHTML.slice(0, 4000) : document.body.innerHTML.slice(0, 2000)};
    },
  };
  chrome.runtime.onMessage.addListener((pedido, _remetente, responder) => {
    const f = acoes[pedido.acao];
    if (!f) { responder({erro: 'acao_desconhecida'}); return; }
    try { responder({resultado: f(pedido.arg)}); } catch (e) { responder({erro: String(e)}); }
  });
  // mantem a extensao acordada enquanto houver uma aba do YouTube aberta
  setInterval(() => chrome.runtime.sendMessage({mestre: 'acorda'}).catch(() => {}), 20000);

  // Avisa o Mestre quando o video desta aba pausa/toca (pelo Mestre OU pela sua mao), para
  // "continua o video" saber, sozinho, em qual aba (a que foi pausada por ultimo).
  let videoObservado = null;
  function avisarEstado(pausado) {
    chrome.runtime.sendMessage({mestre: 'video_estado', pausado}).catch(() => {});
  }
  function observarVideo() {
    const v = document.querySelector('video');
    if (v === videoObservado) return;
    videoObservado = v;
    if (!v) return;
    v.addEventListener('pause', () => avisarEstado(true));
    v.addEventListener('play', () => avisarEstado(false));
    if (!v.paused) avisarEstado(false);
  }
  observarVideo();
  new MutationObserver(observarVideo).observe(document.documentElement, {childList: true, subtree: true});
})();
