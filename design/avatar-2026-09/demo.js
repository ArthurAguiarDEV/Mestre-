/* Página de teste do personagem: monta o boneco, mostra como ele fala e se mexe e deixa arrastar pela tela.
 * Depende de personagem.js (runtime) e dos dados embutidos (#dados). Nada é enviado para fora: tudo roda aqui. */
(function () {
  "use strict";
  const P = window.Personagem;
  const DADOS = JSON.parse(document.getElementById("dados").textContent);
  const D = DADOS.catalogo, A = DADOS.animacao, FALAS = DADOS.falas, JEITOS = DADOS.jeitos, GESTOS = DADOS.gestos;
  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const guardar = (k, v) => { try { localStorage.setItem("personagem." + k, JSON.stringify(v)); } catch (e) { /* sem armazenamento: tudo bem */ } };
  const ler = (k, pad) => { try { const v = localStorage.getItem("personagem." + k); return v == null ? pad : JSON.parse(v); } catch (e) { return pad; } };

  // ---- estado da página --------------------------------------------------------------------------------
  const perfilInicial = Object.assign({}, P.PERFIL_PADRAO, { genero: "m", cabelo: "espetado", cabelo_cor: "castanho", roupa: "moletom", roupa_cor1: "cinza", roupa_cor2: "laranja", roupa_cor3: "preto" });
  let perfil = P.normalizar(ler("perfil", perfilInicial), D);
  let jeito = ler("jeito", "parceiro");
  if (!(jeito in A.arquetipos)) jeito = "parceiro";
  let passeioModo = ler("passeio", "personalidade");
  let estadoManual = "idle";
  let usarVoz = ler("voz", true), passear = ler("passear", true), seguirMouse = ler("mouse", true);
  let abaAtual = ler("aba", "corpo");
  let desenho, anim, passeio, cena;

  // ---- palco (o boneco no canto da tela) -----------------------------------------------------------------
  const FOLGA = 18, ALT_PADRAO = 176, MEIA_LARG = 96, ALT_BALAO = 44, VAO = 8, LARG_BALAO = 440;
  function dimensoes(escala) {
    const alt = ALT_PADRAO * escala, es = alt / P.ALTURA_BASE, lp = 2 * MEIA_LARG * es;
    return { alt, es, lp, largura: Math.ceil(Math.max(lp + 2 * (FOLGA + 34), LARG_BALAO)), altura: Math.ceil(alt + 2 * FOLGA + 24 + ALT_BALAO + VAO) };
  }
  const palco = $("#palco"), ctx = palco.getContext("2d");
  let dim = dimensoes(1), dpr = 1, larguraCss = 440;
  let posSalva = ler("pos", null); // onde o usuário largou o boneco (só arrastar grava)
  let pos = posSalva ? { x: posSalva.x, y: posSalva.y } : null; // {x, y} do canto superior esquerdo do palco

  function medirPalco() {
    dim = dimensoes(perfil.escala);
    dpr = Math.max(1, Math.min(3, window.devicePixelRatio || 1));
    larguraCss = Math.min(dim.largura, Math.max(120, window.innerWidth - 8));
    palco.style.width = larguraCss + "px"; palco.style.height = dim.altura + "px";
    palco.width = Math.round(larguraCss * dpr); palco.height = Math.round(dim.altura * dpr);
  }
  function posPadrao() { return { x: window.innerWidth - larguraCss - 6 + FOLGA, y: window.innerHeight - dim.altura - 6 + FOLGA }; }
  const limitesY = () => [dim.alt + FOLGA + 4 - dim.altura, window.innerHeight - dim.altura + FOLGA + 4];
  function ajustarPos() {
    if (!pos) pos = posPadrao();
    const off = larguraCss - FOLGA - dim.lp;   // onde começa o corpo dentro do palco
    pos.x = Math.min(Math.max(pos.x + off, 0), Math.max(0, window.innerWidth - dim.lp)) - off;
    const [ymin, ymax] = limitesY();
    pos.y = Math.min(Math.max(pos.y, ymin), Math.max(ymin, ymax));
    palco.style.left = pos.x + "px"; palco.style.top = pos.y + "px";
  }
  const refPasseio = () => [pos.x + larguraCss - FOLGA - dim.lp, pos.y];

  function reconstruir(recriarAnimador = true) {
    cena = P.montar(perfil, D);
    desenho = new P.Desenhista(cena);
    medirPalco();
    const traje = perfil.traje ? D.trajes[perfil.traje] : null;
    if (recriarAnimador || !anim || anim.arqId !== jeito || anim._traje !== perfil.traje) {
      const est = anim ? anim.estado : "idle";
      anim = new P.Animador(A, jeito, traje && traje.expressao, (Date.now() & 0xffff));
      anim._traje = perfil.traje;
      anim.mudar(est, agora());
      anim.gesto(A.arquetipos[jeito].chegada, agora() + 0.2);
    }
    anim.balanco = cena.balanco;
    const arq = A.arquetipos[jeito];
    const modo = passeioModo === "personalidade" ? arq.passeio.modo : passeioModo;
    passeio = new P.Passeio(modo, arq.passeio.alcance * perfil.escala, arq.passeio.vel * perfil.escala, arq.passeio.pausa);
    ajustarPos();
    passeio.novoLugar(...refPasseio());
    guardar("perfil", perfil); guardar("jeito", jeito); guardar("passeio", passeioModo);
    atualizarYaml();
  }
  const agora = () => performance.now() / 1000;

  // ---- desenho do quadro ----------------------------------------------------------------------------------
  const TEXTO_ESTADO = { idle: "", ouvindo: "Ouvindo…", pensando: "Pensando…", falando: "Falando…", descansando: "Descansando" };
  const COR_ESTADO = { idle: "#7DE3B8", ouvindo: "#7DE3B8", pensando: "#b388ff", falando: "#4fd1c5", descansando: "#8a8f99" };
  let entrada = 0; // instante em que o boneco entrou (animação de aparecer)

  function pintar(t) {
    const q = anim.quadro(t);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, larguraCss, dim.altura);
    const fx = larguraCss - FOLGA - dim.lp / 2, fy = dim.altura - FOLGA - 4;
    const e = Math.min(1, (t - entrada) / 0.9);
    ctx.save();
    ctx.translate(fx, fy);
    ctx.scale(dim.es, dim.es);
    ctx.globalAlpha = Math.min(1, e * 1.6);
    ctx.translate(0, (1 - suave(e)) * 60);
    if (q.extras.aura) aura(q.extras.aura, t);
    desenho.desenhar(ctx, q.pose);
    extras(q.extras, t, anim.estado);
    ctx.restore();
    const texto = TEXTO_ESTADO[anim.estado];
    if (texto) balao(texto, COR_ESTADO[anim.estado]);
    return q;
  }
  const suave = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  function aura(cor, t) {
    const g = ctx.createRadialGradient(0, -105, 0, 0, -105, 120);
    const a = 0.22 + 0.06 * Math.sin(t * 2.2);
    g.addColorStop(0, cor + Math.round(a * 255).toString(16).padStart(2, "0")); g.addColorStop(1, cor + "00");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, -105, 120, 0, Math.PI * 2); ctx.fill();
  }
  function extras(ex, t, estado) {
    const base = ctx.globalAlpha;
    if (ex.ondas > 0.01) {
      ctx.globalAlpha = base * ex.ondas; ctx.fillStyle = "#7DE3B8";
      [[70, 26], [82, 40], [94, 22]].forEach(([x, alt], i) => {
        const h = alt * (0.35 + 0.65 * (estado === "falando" ? ex.amp : 0.5 + 0.5 * Math.sin(t * 7 + i * 2)));
        ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, -150 - h / 2, 6, h, 3) : ctx.rect(x, -150 - h / 2, 6, h); ctx.fill();
      });
    }
    if (ex.pensando > 0.01) {
      ctx.save(); ctx.globalAlpha = base * ex.pensando; const k = 0.4 + 0.6 * ex.pensando;
      ctx.translate(-70, -218); ctx.scale(k, k);
      ctx.fillStyle = "#2A1F25"; ctx.strokeStyle = "rgba(179,136,255,.8)"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(-34, -18, 68, 32, 16) : ctx.rect(-34, -18, 68, 32); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(24, 22, 5.5, 5, 0, 0, 7); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(32, 32, 3.4, 3, 0, 0, 7); ctx.fill(); ctx.stroke();
      [-16, 0, 16].forEach((x, i) => {
        const f = ((t - i * 0.15) / 1.1) % 1, salto = -5 * (f < 0.6 ? Math.sin(Math.PI * f / 0.6) : 0);
        ctx.fillStyle = "rgba(179,136,255," + (0.55 + 0.45 * (salto / -5)) + ")";
        ctx.beginPath(); ctx.arc(x, -2 + salto, 4.4, 0, 7); ctx.fill();
      });
      ctx.restore();
    }
    if (ex.zzz > 0.01) {
      ctx.fillStyle = "#E7C6F0";
      for (let i = 0; i < 3; i++) {
        const f = ((t - i) / 3) % 1, op = f < 0.25 ? f / 0.25 : 1 - (f - 0.25) / 0.75;
        ctx.globalAlpha = base * ex.zzz * Math.max(0, op); ctx.font = "800 " + Math.round(18 + 8 * f) + "px Fredoka, sans-serif";
        ctx.fillText("z", 64 + 12 * f, -178 - 40 * f);
      }
    }
    if (ex.notas > 0.01) {
      ctx.fillStyle = "#7DE3B8"; ctx.font = "20px sans-serif";
      for (let i = 0; i < 3; i++) { const f = ((t - i * 0.5) / 1.6) % 1; ctx.globalAlpha = base * ex.notas * (1 - f); ctx.fillText("♪", 64 + 10 * Math.sin(f * 6 + i), -150 - 50 * f); }
    }
    if (ex.holo > 0.01) {
      const cor = ex.aura || "#5AD7FF"; ctx.globalAlpha = base * ex.holo; ctx.lineWidth = 2; ctx.strokeStyle = cor; ctx.setLineDash([5, 4]);
      [26, 18].forEach((r, i) => { ctx.save(); ctx.translate(-86, -104); ctx.rotate((t * 40 * (i ? -1.6 : 1) * Math.PI) / 180); ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.55, 0, 0, 7); ctx.stroke(); ctx.restore(); });
      ctx.setLineDash([]); ctx.fillStyle = cor; ctx.globalAlpha = base * ex.holo * 0.16;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(-112, -134 + 3 * Math.sin(t * 3), 52, 34, 6) : ctx.rect(-112, -134, 52, 34); ctx.fill();
    }
    ctx.globalAlpha = base;
  }
  function balao(texto, cor) {
    ctx.save();
    ctx.font = "600 15px 'DM Sans', system-ui, sans-serif";
    const larg = Math.max(70, ctx.measureText(texto).width + 40), h = ALT_BALAO - 8, x = larguraCss - FOLGA - larg, y = 6;
    ctx.globalAlpha = 0.94; ctx.fillStyle = "#1C1418"; ctx.strokeStyle = cor; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, larg, h, h / 2) : ctx.rect(x, y, larg, h); ctx.fill(); ctx.stroke();
    ctx.globalAlpha = 1; ctx.fillStyle = cor; ctx.beginPath(); ctx.arc(x + 14, y + h / 2, 5, 0, 7); ctx.fill();
    ctx.fillStyle = "#F5F5F7"; ctx.textBaseline = "middle"; ctx.fillText(texto, x + 26, y + h / 2 + 1);
    ctx.restore();
  }

  // ---- laço de animação --------------------------------------------------------------------------------------
  function laco() {   // no navegador pinta todo quadro da tela (liso); o app economiza com anim.fps()
    const t = agora();
    if (!document.hidden) {
      anim.mudar(estadoManual, t);
      const ocupado = anim.estado !== "idle" || anim.overlay !== null;
      if (passear && pos) {
        const [ymin, ymax] = limitesY(), area = [0, ymin, window.innerWidth, Math.max(ymin, ymax)];
        const [x, y] = refPasseio();
        const [nx, ny, dir] = passeio.atualizar(t, x, y, area, ocupado || arrastando, dim.lp);
        if (nx !== x || ny !== y) { pos.x = nx - (larguraCss - FOLGA - dim.lp); pos.y = ny; palco.style.left = pos.x + "px"; palco.style.top = pos.y + "px"; }
        anim.andar(dir, passeio.vel / 70);
      } else anim.andar(0);
      pintar(t);
    }
    requestAnimationFrame(laco);
  }

  // ---- arrastar e reagir ------------------------------------------------------------------------------------------
  let arrastando = false, deslocamento = null, moveu = false;
  palco.addEventListener("pointerdown", (e) => {
    arrastando = true; moveu = false; deslocamento = [e.clientX - pos.x, e.clientY - pos.y]; palco.setPointerCapture(e.pointerId); palco.classList.add("pegando");
  });
  palco.addEventListener("pointermove", (e) => {
    if (!arrastando) return;
    const nx = e.clientX - deslocamento[0], ny = e.clientY - deslocamento[1];
    if (Math.abs(nx - pos.x) + Math.abs(ny - pos.y) > 2) moveu = true;
    pos.x = nx; pos.y = ny; ajustarPos();
  });
  const soltar = () => {
    if (!arrastando) return;
    arrastando = false; palco.classList.remove("pegando");
    if (moveu) { posSalva = { x: pos.x, y: pos.y }; guardar("pos", posSalva); }
    passeio.novoLugar(...refPasseio());
    if (!moveu && !anim.ocupado()) anim.gesto(anim.rng.escolher([["surpresa", 2], ["acenar", 2], ["pular", 1]]), agora());
  };
  palco.addEventListener("pointerup", soltar); palco.addEventListener("pointercancel", soltar);
  window.addEventListener("pointermove", (e) => {
    if (!seguirMouse || !pos) return;
    const cx = pos.x + larguraCss - FOLGA - dim.lp / 2, cy = pos.y + dim.altura - FOLGA - dim.alt / 2;
    anim.olhar((e.clientX - cx) / 500, (e.clientY - (cy - dim.alt * 0.2)) / 320);
  });
  window.addEventListener("resize", () => { medirPalco(); if (!posSalva) pos = posPadrao(); ajustarPos(); passeio.novoLugar(...refPasseio()); });

  // ---- fala -----------------------------------------------------------------------------------------------------------
  let fimFala = null;
  function falar(frase) {
    frase = (frase || "").trim(); if (!frase) return;
    cancelarFala();
    anim.texto(frase);
    estadoManual = "falando"; marcarEstado();
    const fim = () => { if (estadoManual === "falando") { estadoManual = "idle"; marcarEstado(); } };
    if (usarVoz && "speechSynthesis" in window) {
      try {
        const u = new SpeechSynthesisUtterance(frase);
        u.lang = "pt-BR"; const v = speechSynthesis.getVoices().find((x) => /^pt(-|_)BR/i.test(x.lang)); if (v) u.voice = v;
        const j = JEITOS[jeito]; u.rate = j.taxa; u.pitch = j.tom;
        u.onend = fim; u.onerror = fim; speechSynthesis.cancel(); speechSynthesis.speak(u);
        fimFala = setTimeout(fim, 2000 + frase.length * 140);
        return;
      } catch (e) { /* cai para a fala em silêncio */ }
    }
    fimFala = setTimeout(fim, 700 + frase.length * 62);
  }
  function cancelarFala() { if (fimFala) clearTimeout(fimFala); fimFala = null; try { if ("speechSynthesis" in window) speechSynthesis.cancel(); } catch (e) { /* nada */ } }
  const fraseDoJeito = () => { const f = FALAS[jeito]; const grupos = ["chamado", "ok", "obrigado", "inicio", "nao_entendi"]; const lista = f[grupos[Math.floor(Math.random() * grupos.length)]]; return lista[Math.floor(Math.random() * lista.length)]; };

  // ---- interface: abas e painéis ----------------------------------------------------------------------------
  const ABAS = [["corpo", "Corpo"], ["rosto", "Rosto"], ["cabelo", "Cabelo"], ["roupa", "Roupa"], ["fantasia", "Fantasia"], ["extras", "Extras"], ["jeito", "Jeito"]];
  const painelEl = $("#conteudo"), abasEl = $("#abas");

  function miniatura(perfilParcial, modo) {
    const c = el("canvas", "mini"); const W = 72, H = modo === "rosto" ? 72 : 96; c.width = W * 2; c.height = H * 2; c.style.width = W + "px"; c.style.height = H + "px";
    const x = c.getContext("2d"); x.scale(2, 2);
    const cena2 = P.montar(Object.assign({}, perfil, perfilParcial), D), d = new P.Desenhista(cena2);
    x.save();
    if (modo === "rosto") { const es = 0.58; x.translate(W / 2, H / 2 + 150 * es); x.scale(es, es); }
    else { const es = (H - 8) / 214; x.translate(W / 2, H - 4); x.scale(es, es); }
    d.desenhar(x, {});
    x.restore();
    return c;
  }
  function paleta(lista, atual, aoEscolher, nomeGrupo) {
    const g = el("div", "amostras"); g.setAttribute("role", "radiogroup"); g.setAttribute("aria-label", nomeGrupo);
    for (const [id, nome, corHex] of lista) {
      const b = el("button", "amostra"); b.type = "button"; b.style.background = corHex; b.title = nome; b.setAttribute("aria-label", nome); b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(atual === id));
      b.addEventListener("click", () => aoEscolher(id)); g.appendChild(b);
    }
    return g;
  }
  function campo(titulo, dica) { const s = el("div", "campo"); s.appendChild(el("h3", "campo-t", titulo)); if (dica) s.appendChild(el("p", "dica", dica)); return s; }
  function grade(itens, atual, aoEscolher, modo, parcial, multi) {
    const g = el("div", "grade-thumbs");
    for (const [id, nome, extraCls] of itens) {
      const b = el("button", "thumb" + (extraCls ? " " + extraCls : "")); b.type = "button";
      const marcado = multi ? atual.includes(id) : atual === id;
      b.setAttribute("aria-pressed", String(marcado));
      if (id === "") b.appendChild(el("span", "sem", "—")); else b.appendChild(miniatura(parcial(id), modo));
      b.appendChild(el("span", "thumb-n", nome)); b.addEventListener("click", () => aoEscolher(id)); g.appendChild(b);
    }
    return g;
  }
  function mudarPerfil(parte, recriarAnimador = false) { perfil = P.normalizar(Object.assign({}, perfil, parte), D); reconstruir(recriarAnimador); desenharPainel(); }

  function desenharPainel() {
    abasEl.querySelectorAll("button").forEach((b) => { const ativo = b.dataset.aba === abaAtual; b.setAttribute("aria-selected", String(ativo)); b.tabIndex = ativo ? 0 : -1; });
    painelEl.replaceChildren();
    const aba = abaAtual;
    if (aba === "corpo") {
      let c = campo("Quem é", "Escolha o corpo. Cabelo, roupa e fantasias funcionam nos dois.");
      const linha = el("div", "duas");
      for (const [g, nome] of [["m", "Homem"], ["f", "Mulher"]]) {
        const b = el("button", "grande"); b.type = "button"; b.setAttribute("aria-pressed", String(perfil.genero === g));
        b.appendChild(miniatura({ genero: g, traje: "", acessorios: [] }, "corpo")); b.appendChild(el("span", "thumb-n", nome));
        b.addEventListener("click", () => mudarPerfil({ genero: g, cabelo: perfil.cabelo })); linha.appendChild(b);
      }
      c.appendChild(linha); painelEl.appendChild(c);
      c = campo("Tom de pele"); c.appendChild(paleta(D.peles, perfil.pele, (id) => mudarPerfil({ pele: id }), "Tom de pele")); painelEl.appendChild(c);
      c = campo("Cor dos olhos"); c.appendChild(paleta(D.cores_olhos, perfil.olhos_cor, (id) => mudarPerfil({ olhos_cor: id }), "Cor dos olhos")); painelEl.appendChild(c);
      c = campo("Tamanho", "100% = 176 px de altura na tela (o bonequinho do jogo tem uns 55 px).");
      const r = el("input", "faixa"); r.type = "range"; r.id = "tamanho"; r.min = "60"; r.max = "160"; r.step = "5"; r.value = String(Math.round(perfil.escala * 100)); r.setAttribute("aria-label", "Tamanho do personagem");
      const v = el("output", "valor", r.value + "%"); r.addEventListener("input", () => { v.textContent = r.value + "%"; });
      r.addEventListener("change", () => mudarPerfil({ escala: r.value / 100 }));
      const l = el("div", "faixa-linha"); l.append(r, v); c.appendChild(l); painelEl.appendChild(c);
    } else if (aba === "rosto") {
      for (const opc of D.rosto_ordem) {
        const c = campo(D.rosto_rotulos[opc]);
        c.appendChild(grade(Object.entries(D.rosto.m[opc]).map(([id, o]) => [id, o.nome]), perfil[opc], (id) => mudarPerfil({ [opc]: id }), "rosto",
          (id) => ({ [opc]: id, traje: "", acessorios: [] })));
        painelEl.appendChild(c);
      }
      if (perfil.traje) painelEl.appendChild(el("p", "aviso", "Com fantasia, o rosto fica redondo (as máscaras foram desenhadas nele)."));
    } else if (aba === "cabelo") {
      let c = campo("Estilo"); c.appendChild(grade(Object.entries(D.cabelos).map(([id, o]) => [id, o.nome]), perfil.cabelo, (id) => mudarPerfil({ cabelo: id }), "rosto", (id) => ({ cabelo: id, traje: "", acessorios: [] })));
      painelEl.appendChild(c);
      c = campo("Cor do cabelo"); c.appendChild(paleta(D.cores_cabelo, perfil.cabelo_cor, (id) => mudarPerfil({ cabelo_cor: id }), "Cor do cabelo")); painelEl.appendChild(c);
      if (perfil.traje && ((D.trajes[perfil.traje].esconde || []).includes("cabelo") || D.trajes[perfil.traje].forca_cabelo)) painelEl.appendChild(el("p", "aviso", "A fantasia " + D.trajes[perfil.traje].nome + " manda no cabelo. Tire a fantasia para ver o seu."));
    } else if (aba === "roupa") {
      let c = campo("Roupa do dia a dia");
      c.appendChild(grade(Object.entries(D.roupas).map(([id, o]) => [id, o.nome]), perfil.roupa, (id) => { const cores = D.roupas[id].cores; mudarPerfil({ roupa: id, roupa_cor1: cores[0], roupa_cor2: cores[1], roupa_cor3: cores[2], traje: "" }); }, "corpo", (id) => { const cores = D.roupas[id].cores; return { roupa: id, roupa_cor1: cores[0], roupa_cor2: cores[1], roupa_cor3: cores[2], traje: "", acessorios: [] }; }));
      painelEl.appendChild(c);
      for (const [chave, nome] of [["roupa_cor1", "Peça de cima"], ["roupa_cor2", "Detalhes"], ["roupa_cor3", "Parte de baixo"]]) {
        c = campo(nome); c.appendChild(paleta(D.cores_roupa, perfil[chave], (id) => mudarPerfil({ [chave]: id, traje: "" }), nome)); painelEl.appendChild(c);
      }
      if (perfil.traje) painelEl.appendChild(el("p", "aviso", "Escolher uma roupa tira a fantasia."));
    } else if (aba === "fantasia") {
      const semTraje = campo("Fantasia", "Heróis inspirados (cores e formas simples, só para uso pessoal) e fantasias clássicas.");
      semTraje.appendChild(grade([["", "Sem fantasia"]], perfil.traje, () => mudarPerfil({ traje: "" }), "corpo", () => ({})));
      painelEl.appendChild(semTraje);
      for (const uni of D.universos) {
        const c = campo(uni);
        const itens = Object.entries(D.trajes).filter(([, t]) => t.universo === uni).map(([id, t]) => [id, t.nome]);
        c.appendChild(grade(itens, perfil.traje, (id) => mudarPerfil({ traje: id }), "corpo", (id) => ({ traje: id, acessorios: [] })));
        painelEl.appendChild(c);
      }
    } else if (aba === "extras") {
      const c = campo("Acessórios", "Pode escolher vários. Fantasias com máscara escondem os que ficam no rosto.");
      c.appendChild(grade(Object.entries(D.acessorios).map(([id, o]) => [id, o.nome]), perfil.acessorios, (id) => {
        const ja = perfil.acessorios.includes(id); mudarPerfil({ acessorios: ja ? perfil.acessorios.filter((x) => x !== id) : perfil.acessorios.concat(id) });
      }, "rosto", (id) => ({ traje: "", acessorios: [id] }), true));
      painelEl.appendChild(c);
    } else if (aba === "jeito") {
      const c = campo("Jeito do personagem", "Cada personalidade do Assessor mexe, fala e fica na tela de um jeito. No Assessor, o jeito acompanha a personalidade escolhida.");
      const lista = el("div", "jeitos");
      for (const id of Object.keys(A.arquetipos)) {
        const j = JEITOS[id], b = el("button", "jeito"); b.type = "button"; b.setAttribute("aria-pressed", String(jeito === id));
        b.appendChild(el("span", "jeito-n", j.nome)); b.appendChild(el("span", "jeito-e", "Assessor: " + j.estilo)); b.appendChild(el("span", "jeito-d", j.descricao));
        b.addEventListener("click", () => { jeito = id; reconstruir(true); desenharPainel(); }); lista.appendChild(b);
      }
      c.appendChild(lista); painelEl.appendChild(c);
      const p = campo("Passeio pela tela", "Onde o boneco anda quando você não está falando com ele.");
      const sel = el("select", "seletor"); sel.id = "passeio-modo"; sel.setAttribute("aria-label", "Passeio pela tela");
      for (const [k, n] of Object.entries(DADOS.modos_passeio)) { const o = el("option", null, n); o.value = k; if (k === passeioModo) o.selected = true; sel.appendChild(o); }
      sel.addEventListener("change", () => { passeioModo = sel.value; reconstruir(false); });
      p.appendChild(sel); painelEl.appendChild(p);
    }
  }
  function montarAbas() {
    abasEl.replaceChildren();
    for (const [id, nome] of ABAS) {
      const b = el("button", "aba", nome); b.type = "button"; b.dataset.aba = id; b.setAttribute("role", "tab");
      b.addEventListener("click", () => { abaAtual = id; guardar("aba", id); desenharPainel(); });
      b.addEventListener("keydown", (e) => {
        const i = ABAS.findIndex((a) => a[0] === abaAtual); let n = null;
        if (e.key === "ArrowRight") n = (i + 1) % ABAS.length; if (e.key === "ArrowLeft") n = (i + ABAS.length - 1) % ABAS.length;
        if (n !== null) { abaAtual = ABAS[n][0]; desenharPainel(); abasEl.querySelector('[data-aba="' + abaAtual + '"]').focus(); }
      });
      abasEl.appendChild(b);
    }
  }

  // ---- teste do boneco: estados, fala, gestos ---------------------------------------------------------------------
  function marcarEstado() { document.querySelectorAll("#estados button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.estado === estadoManual))); }
  function montarTeste() {
    const est = $("#estados");
    for (const [id, nome] of [["idle", "Parado"], ["ouvindo", "Ouvindo"], ["pensando", "Pensando"], ["falando", "Falando"], ["descansando", "Descansando"]]) {
      const b = el("button", "seg", nome); b.type = "button"; b.dataset.estado = id;
      b.addEventListener("click", () => { cancelarFala(); estadoManual = id; marcarEstado(); if (id === "falando") anim.texto("Estou falando com você agora"); });
      est.appendChild(b);
    }
    marcarEstado();
    const fr = $("#frase");
    fr.value = "Beleza, deixa comigo. Já abri o que você pediu.";
    $("#falar").addEventListener("click", () => falar(fr.value));
    fr.addEventListener("keydown", (e) => { if (e.key === "Enter") falar(fr.value); });
    $("#sortear-frase").addEventListener("click", () => { fr.value = fraseDoJeito(); falar(fr.value); });
    const g = $("#gestos");
    for (const [id, nome] of GESTOS) {
      const b = el("button", "chip", nome); b.type = "button";
      b.addEventListener("click", () => { estadoManual = "idle"; marcarEstado(); anim.mudar("idle", agora()); anim.gesto(id, agora()); });
      g.appendChild(b);
    }
    const lig = (id, get, set, chave) => { const c = $(id); c.checked = get(); c.addEventListener("change", () => { set(c.checked); guardar(chave, c.checked); }); };
    lig("#usar-voz", () => usarVoz, (v) => { usarVoz = v; if (!v) cancelarFala(); }, "voz");
    lig("#passear", () => passear, (v) => { passear = v; if (v) passeio.novoLugar(...refPasseio()); }, "passear");
    lig("#seguir-mouse", () => seguirMouse, (v) => { seguirMouse = v; if (!v) anim.olhar(0, 0); }, "mouse");
    if (!("speechSynthesis" in window)) { $("#usar-voz").disabled = true; $("#usar-voz").checked = false; usarVoz = false; }
  }

  // ---- configuração para o Assessor -----------------------------------------------------------------------------------
  function yaml() {
    const p = perfil;
    return ["avatar:", '  modelo: "personagem"', '  jeito: "' + jeito + '"', '  passeio: "' + passeioModo + '"', "  personagem:",
      '    genero: "' + p.genero + '"', '    pele: "' + p.pele + '"', '    cabelo: "' + p.cabelo + '"', '    cabelo_cor: "' + p.cabelo_cor + '"',
      '    olhos_cor: "' + p.olhos_cor + '"', '    roupa: "' + p.roupa + '"', '    roupa_cor1: "' + p.roupa_cor1 + '"', '    roupa_cor2: "' + p.roupa_cor2 + '"',
      '    roupa_cor3: "' + p.roupa_cor3 + '"', '    traje: "' + p.traje + '"', "    acessorios: [" + p.acessorios.map((a) => '"' + a + '"').join(", ") + "]",
      "    escala: " + p.escala].concat(D.rosto_ordem.map((opc) => "    " + opc + ': "' + p[opc] + '"')).join("\n");
  }
  function atualizarYaml() { const c = $("#yaml"); if (c) c.textContent = yaml(); }
  function montarConfig() {
    $("#copiar").addEventListener("click", async () => {
      const b = $("#copiar"), t = yaml();
      try { await navigator.clipboard.writeText(t); b.textContent = "Copiado"; } catch (e) { const r = document.createRange(); r.selectNodeContents($("#yaml")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = "Selecionado: use Ctrl+C"; }
      setTimeout(() => { b.textContent = "Copiar"; }, 1800);
    });
    $("#sortear").addEventListener("click", sortear);
    $("#reiniciar").addEventListener("click", () => { perfil = P.normalizar(perfilInicial, D); jeito = "parceiro"; passeioModo = "personalidade"; reconstruir(true); desenharPainel(); });
  }
  const sorteia = (l) => l[Math.floor(Math.random() * l.length)];
  function sortear() {
    const g = Math.random() < 0.5 ? "m" : "f", r = sorteia(Object.keys(D.roupas)), ids = (l) => l.map((x) => x[0]);
    const cores = D.roupas[r].cores;
    const acs = Object.keys(D.acessorios).filter(() => Math.random() < 0.1);
    const rosto = {}; for (const opc of D.rosto_ordem) rosto[opc] = sorteia(Object.keys(D.rosto.m[opc]));
    mudarPerfil({ ...rosto, genero: g, pele: sorteia(ids(D.peles)), cabelo: sorteia(Object.keys(D.cabelos)), cabelo_cor: sorteia(ids(D.cores_cabelo)), olhos_cor: sorteia(ids(D.cores_olhos)),
      roupa: r, roupa_cor1: Math.random() < 0.5 ? cores[0] : sorteia(ids(D.cores_roupa)), roupa_cor2: sorteia(ids(D.cores_roupa)), roupa_cor3: Math.random() < 0.5 ? cores[2] : sorteia(ids(D.cores_roupa)),
      traje: Math.random() < 0.3 ? sorteia(Object.keys(D.trajes)) : "", acessorios: acs.slice(0, 2) }, false);
  }

  // ---- início -------------------------------------------------------------------------------------------------------------
  montarAbas(); montarTeste(); montarConfig();
  reconstruir(true); desenharPainel();
  entrada = agora();
  if ("speechSynthesis" in window) { try { speechSynthesis.getVoices(); } catch (e) { /* nada */ } }
  window.__personagem = { D, A, P, montar: (pf) => P.montar(pf, D), estado: () => ({ perfil, jeito, passeioModo, pos }) };
  requestAnimationFrame(laco);
})();
