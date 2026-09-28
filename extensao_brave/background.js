// Mestre: busca os pedidos do assistente (so no proprio PC) e age nas abas do Brave.
// - abas e janelas (listar, focar, separar uma aba numa janela so dela, abrir janela nova);
// - navegacao (voltar/avancar pagina, proxima/anterior aba);
// - acoes dentro do YouTube (repassadas para conteudo.js na aba do YouTube em uso).
const MESTRE = "http://127.0.0.1:47632";
let rodando = false;
// Estado do video por aba (avisado pelo conteudo.js): {pausado, quando}. Usado por "continua o
// video" para saber, sozinho, qual aba foi pausada por ultimo (mesmo se pausada pela sua mao).
const estadoVideo = new Map();
chrome.tabs.onRemoved.addListener(id => estadoVideo.delete(id));

async function janelaEmUso() {
  try { return await chrome.windows.getLastFocused({windowTypes: ["normal"]}); } catch (e) { return null; }
}

async function abaEmUso() {
  const ativas = await chrome.tabs.query({active: true, lastFocusedWindow: true});
  return ativas[0];
}

async function abaDoYouTube() {
  // 1) a aba que voce esta vendo, se for do YouTube; 2) senao, a do YouTube usada por ultimo
  const ativas = await chrome.tabs.query({active: true, lastFocusedWindow: true, url: "*://*.youtube.com/*"});
  if (ativas.length) return ativas[0];
  const todas = await chrome.tabs.query({url: "*://*.youtube.com/*"});
  todas.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
  return todas[0];
}

async function abaAlvo(arg) {   // a aba pedida (id), senao a do site (dominio) usada por ultimo, senao a que voce esta vendo
  if (arg && arg.aba) { try { return await chrome.tabs.get(arg.aba); } catch (e) { /* fechou: segue */ } }
  if (arg && arg.dominio) {
    const abas = await chrome.tabs.query({url: `*://*.${arg.dominio}/*`});
    abas.sort((a, b) => (b.active - a.active) || ((b.lastAccessed || 0) - (a.lastAccessed || 0)));
    if (abas.length) return abas[0];
  }
  return await abaEmUso();
}

async function focarJanela(id) {
  const j = await chrome.windows.get(id);
  const mudar = {focused: true};
  if (j.state === "minimized") mudar.state = "normal";
  await chrome.windows.update(id, mudar);
}

const noNavegador = {
  async abas() {
    const emUso = await janelaEmUso();
    const janelas = await chrome.windows.getAll({populate: true, windowTypes: ["normal"]});
    return janelas.flatMap(j => j.tabs.map(a => ({
      id: a.id, janela: j.id, titulo: a.title || "", url: a.url || "", ativa: a.active,
      janela_em_uso: !!emUso && emUso.id === j.id, abas_na_janela: j.tabs.length,
      ultimo_acesso: a.lastAccessed || 0, audivel: !!a.audible,
      // video: se esta pausado agora e quando pausou/tocou por ultimo (para "continua o video" escolher a aba)
      video_pausado: estadoVideo.has(a.id) ? estadoVideo.get(a.id).pausado : null,
      video_pausado_em: estadoVideo.has(a.id) ? estadoVideo.get(a.id).quando : 0,
      // onde a janela esta na tela (para saber o monitor) e se esta minimizada
      janela_x: j.left, janela_y: j.top, janela_largura: j.width, janela_altura: j.height, janela_estado: j.state})));
  },
  async focar(id) {
    const a = await chrome.tabs.update(id, {active: true});
    await focarJanela(a.windowId);
    return {titulo: a.title || ""};
  },
  async separar(id) {   // a aba vai para uma janela so dela (se ja estiver sozinha, so foca)
    const a = await chrome.tabs.get(id);
    const j = await chrome.windows.get(a.windowId, {populate: true});
    if (j.tabs.length === 1) {
      await focarJanela(j.id);
      return {titulo: a.title || "", nova: false};
    }
    await chrome.windows.create({tabId: id, focused: true});
    return {titulo: a.title || "", nova: true};
  },
  async nova_janela(url) {
    const j = await chrome.windows.create({url, focused: true});
    return {janela: j.id};
  },
  async voltar() { const a = await abaEmUso(); if (!a) return "sem_aba"; await chrome.tabs.goBack(a.id).catch(() => {}); return "ok"; },
  async avancar() { const a = await abaEmUso(); if (!a) return "sem_aba"; await chrome.tabs.goForward(a.id).catch(() => {}); return "ok"; },
  async trocar_aba(passo) {
    const a = await abaEmUso();
    if (!a) return "sem_aba";
    const abas = await chrome.tabs.query({windowId: a.windowId});
    const alvo = abas[(a.index + passo + abas.length) % abas.length];
    await chrome.tabs.update(alvo.id, {active: true});
    return alvo.title || "";
  },
  async pagina() { const a = await abaEmUso(); return a ? {titulo: a.title || "", url: a.url || ""} : {}; },
  async juntar(arg) {   // leva abas para a janela da aba "destino" (a ultima levada fica na frente)
    const destino = await chrome.tabs.get(arg.destino);
    const ids = (arg.abas || []).filter(id => id !== arg.destino);
    if (!ids.length) return "nada";
    await chrome.tabs.move(ids, {windowId: destino.windowId, index: -1});
    await chrome.tabs.update(ids[ids.length - 1], {active: true});
    await focarJanela(destino.windowId);
    return "ok";
  },
  async ir(arg) {   // abre o endereco na aba do site (se ja existir) ou numa aba nova da janela em uso
    const abas = arg.dominio ? await chrome.tabs.query({url: `*://*.${arg.dominio}/*`}) : [];
    abas.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
    let aba;
    if (abas.length) {
      aba = await chrome.tabs.update(abas[0].id, {url: arg.url, active: true});
      await focarJanela(aba.windowId);
    } else {
      const j = await janelaEmUso();
      aba = await chrome.tabs.create(j ? {url: arg.url, windowId: j.id} : {url: arg.url});
      if (j) await focarJanela(j.id);
    }
    return {id: aba.id};
  },
  async clicar(arg) {   // clica num botao/link pelo texto que aparece na tela ("continuar assistindo")
    const aba = await abaAlvo(arg);
    if (!aba) return "sem_aba";
    const [r] = await chrome.scripting.executeScript({target: {tabId: aba.id}, func: clicarPorTexto,
                                                      args: [arg.textos || [], arg.modo || "", !!arg.so_ver]});
    return r ? r.result : "nao_achei";
  },
  async buscar(arg) {   // digita no campo de busca do site (Disney, HBO...); sem campo, clica na lupa
    const aba = await abaAlvo(arg);
    if (!aba) return "sem_aba";
    if (aba.status === "loading") return "carregando";
    const [r] = await chrome.scripting.executeScript({target: {tabId: aba.id}, func: digitarNaBusca, args: [arg.texto || ""]});
    return r ? r.result : "sem_busca";
  },
};

// (roda DENTRO da pagina) acha o campo de busca e escreve o texto como se fosse digitado
function digitarNaBusca(texto) {
  const todos = seletor => {
    const achados = [], fila = [document];
    while (fila.length) {
      const raiz = fila.shift();
      achados.push(...raiz.querySelectorAll(seletor));
      for (const el of raiz.querySelectorAll("*")) if (el.shadowRoot) fila.push(el.shadowRoot);
    }
    return achados;
  };
  const norm = s => (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
  const visivel = el => { const r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2 && getComputedStyle(el).visibility !== "hidden"; };
  const BUSCA = /(search|busca|buscar|pesquis|procur)/;
  const dados = el => norm([el.id, el.name, el.placeholder, el.getAttribute("aria-label"), el.getAttribute("data-testid"),
                            el.getAttribute("title"), typeof el.className === "string" ? el.className : ""].join(" "));
  const campos = todos("input, textarea").filter(el => visivel(el) && !el.disabled && !el.readOnly &&
    !["hidden", "checkbox", "radio", "submit", "button", "password", "email", "tel", "number"].includes((el.type || "").toLowerCase()));
  let campo = campos.find(el => (el.type || "").toLowerCase() === "search" || BUSCA.test(dados(el)));
  if (!campo && campos.length === 1 && BUSCA.test(location.pathname + location.hash)) campo = campos[0];
  if (campo) {
    if (norm(campo.value) === norm(texto)) return "ja";
    campo.focus();
    const proto = campo instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(campo, texto);   // (React e parecidos so veem assim)
    campo.dispatchEvent(new InputEvent("input", {bubbles: true, composed: true, data: texto, inputType: "insertText"}));
    campo.dispatchEvent(new Event("change", {bubbles: true}));
    for (const tipo of ["keydown", "keypress", "keyup"]) {
      campo.dispatchEvent(new KeyboardEvent(tipo, {key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, composed: true}));
    }
    return "digitei";
  }
  // sem campo na tela: a lupa / o link "Pesquisa" do menu
  const lupa = todos('a, button, [role="button"], [role="link"], [role="menuitem"], [role="tab"]').filter(visivel).find(el =>
    BUSCA.test(norm([el.getAttribute("aria-label"), el.getAttribute("title"), el.getAttribute("data-testid"), el.id,
                     (el.innerText || "").slice(0, 30), el.getAttribute("href")].join(" "))));
  if (lupa) { lupa.click(); return "abri_busca"; }
  return "sem_busca";
}

// (roda DENTRO da pagina) acha o elemento visivel cujo texto combina melhor e clica.
// modo "titulo": prefere capas/links de filme e serie (e nao as "pesquisas recentes").
// soVer: so diz se achou ({nota, texto}), sem clicar (para escolher a janela certa).
function clicarPorTexto(alvos, modo, soVer) {
  const todos = seletor => {
    const achados = [], fila = [document];
    while (fila.length) {
      const raiz = fila.shift();
      achados.push(...raiz.querySelectorAll(seletor));
      for (const el of raiz.querySelectorAll("*")) if (el.shadowRoot) fila.push(el.shadowRoot);
    }
    return achados;
  };
  const norm = s => (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/[^a-z0-9 ]+/g, "").replace(/\s+/g, " ").trim();
  // parecido: as palavras faladas aparecem no texto (aceita plural: "shields" x "S.H.I.E.L.D.")
  const palavras = s => s.split(" ").filter(w => w.length > 2 && !["das", "dos", "the", "and", "com"].includes(w))
    .map(w => w.replace(/s$/, ""));
  const parecido = (a, t) => {
    const pa = palavras(a), pt = palavras(t);
    if (!pa.length) return 0;
    return pa.filter(w => pt.some(x => x === w || (w.length >= 4 && x.startsWith(w)) || (x.length >= 4 && w.startsWith(x)))).length / pa.length;
  };
  const CONTEUDO = /\/(series|serie|movies?|filmes?|title|titulo|detail|details|browse\/entity|video|videos|play|watch|programa|program|dp|gp\/video|show|episod)/i;
  const candidatos = todos('a, button, [role="button"], [role="link"], [role="menuitem"], [role="tab"], [tabindex], img[alt]');
  for (const alvo of alvos) {
    const a = norm(alvo);
    if (!a) continue;
    let melhor = null, nota = 0;
    for (const el of candidatos) {
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.bottom < 0 || r.top > innerHeight * 3) continue;
      const t = norm(el.getAttribute("aria-label") || el.getAttribute("alt") || el.getAttribute("title") || el.innerText);
      if (!t || t.length > 160) continue;
      let n = t === a ? 4 : t.startsWith(a) ? 3 : t.includes(a) ? 2 : (a.includes(t) && t.length > 4) ? 1 :
              parecido(a, t) >= 0.75 ? 1 : 0;
      if (n && modo === "titulo") {
        const link = el.closest("a");
        if ((link && CONTEUDO.test(link.getAttribute("href") || "")) || el.tagName === "IMG" || el.querySelector("img")) n += 3;
        // "pesquisas recentes" / sugestoes so repetem a busca: nao sao o filme
        if (el.closest('[class*="recent" i], [class*="suggest" i], [class*="history" i], [data-testid*="recent" i]')) n = 0;
      }
      if (n > nota) { nota = n; melhor = el; }
    }
    if (melhor) {
      const texto = (melhor.getAttribute("aria-label") || melhor.getAttribute("alt") || melhor.innerText || "ok").trim().slice(0, 80);
      if (soVer) return {nota, texto};
      const alvoClique = melhor.closest('a, button, [role="button"], [role="link"]') || melhor;
      alvoClique.scrollIntoView({block: "center"});
      alvoClique.click();
      return texto;
    }
  }
  return soVer ? {nota: 0, texto: ""} : "nao_achei";
}

async function executar(pedido) {
  const f = noNavegador[pedido.acao];
  if (f) return {resultado: await f(pedido.arg)};
  // daqui para baixo: coisas do YouTube (na aba pedida pelo Mestre, senao na do YouTube em uso)
  let aba = null;
  if (pedido.aba) { try { aba = await chrome.tabs.get(pedido.aba); } catch (e) { aba = null; } }
  if (!aba) aba = await abaDoYouTube();
  if (!aba) return {erro: "sem_aba"};
  if (pedido.acao === "abrir") {
    await chrome.tabs.update(aba.id, {url: pedido.arg, active: true});
    return {ok: true};
  }
  if (pedido.acao === "endereco") return {resultado: aba.url};
  if (pedido.acao === "focar_youtube") {   // antes das teclas (tela cheia, cinema...): a aba certa na frente
    await chrome.tabs.update(aba.id, {active: true});
    await focarJanela(aba.windowId);
    return {resultado: aba.title || ""};
  }
  try {
    return await chrome.tabs.sendMessage(aba.id, pedido);
  } catch (e) {
    return {erro: "aba_sem_extensao: recarregue a pagina do YouTube (F5)"};
  }
}

async function laco() {
  if (rodando) return;
  rodando = true;
  try {
    while (true) {
      let resp;
      try {
        resp = await fetch(MESTRE + "/proximo?v=" + chrome.runtime.getManifest().version, {cache: "no-store"});
      } catch (e) {            // o Mestre esta desligado: tenta de novo daqui a pouco
        await new Promise(r => setTimeout(r, 5000));
        continue;
      }
      if (resp.status !== 200) continue;
      const pedido = await resp.json();
      let resultado;
      try {
        resultado = await executar(pedido);
      } catch (e) {
        resultado = {erro: String(e)};
      }
      await fetch(MESTRE + "/resposta", {method: "POST", headers: {"Content-Type": "application/json"},
                                          body: JSON.stringify({id: pedido.id, ...resultado})}).catch(() => {});
    }
  } finally {
    rodando = false;
  }
}

chrome.runtime.onStartup.addListener(laco);
chrome.runtime.onInstalled.addListener(laco);
chrome.alarms.create("mestre", {periodInMinutes: 0.5});
chrome.alarms.onAlarm.addListener(laco);
chrome.runtime.onMessage.addListener((msg, remetente) => {
  if (msg && msg.mestre === "acorda") laco();
  else if (msg && msg.mestre === "video_estado" && remetente && remetente.tab) {
    estadoVideo.set(remetente.tab.id, {pausado: !!msg.pausado, quando: Date.now()});
  }
});
laco();
