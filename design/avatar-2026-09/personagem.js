/* Personagem do Assessor — runtime da página de teste (Canvas 2D).
 * Repete, em poucas linhas, o que o app faz em Python (app/personagem/): monta a cena a partir do perfil (cena.py),
 * desenha (render_qt.py), anima (animacao.py), passeia (passeio.py). Os DADOS (catálogo, clipes, personalidades) são os
 * mesmos: vêm do catálogo em Python. O sorteio (mulberry32) e as contas de cor são idênticos, e o teste automático
 * confere se a cena montada aqui bate com a do Python.
 */
(function (raiz) {
  "use strict";
  const PI2 = Math.PI * 2;
  const lim = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  const suave = (x) => { x = lim(x); return x * x * (3 - 2 * x); };

  // ---- cores -----------------------------------------------------------------------------------------
  const rgb = (h) => { h = h.replace("#", ""); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  const hex = (r, g, b) => "#" + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.floor(v + 0.5))).toString(16).toUpperCase().padStart(2, "0")).join("");
  function misturar(a, b, k) { const x = rgb(a), y = rgb(b); return hex(x[0] + (y[0] - x[0]) * k, x[1] + (y[1] - x[1]) * k, x[2] + (y[2] - x[2]) * k); }
  function resolverCor(tok, pal) {
    if (tok == null) return tok;
    const m = /^(#[0-9A-Fa-f]{6}|\$[a-z0-9_]+)([+-]*)$/.exec(tok);
    if (!m) throw new Error("cor inválida: " + tok);
    let base = m[1][0] === "#" ? m[1].toUpperCase() : pal[m[1].slice(1)];
    for (const ch of m[2]) base = ch === "+" ? misturar(base, "#FFFFFF", 0.22) : misturar(base, "#1A0F14", 0.24);
    return base.toUpperCase();
  }
  function resolverPrim(p, pal) {
    const q = Object.assign({}, p);
    if (Array.isArray(p.f)) q.f = [p.f[0]].concat(p.f.slice(1).map((c) => resolverCor(c, pal)));
    else if (p.f) q.f = resolverCor(p.f, pal);
    if (p.s) q.s = resolverCor(p.s, pal);
    return q;
  }
  const clone = (o) => JSON.parse(JSON.stringify(o));

  // ---- cena --------------------------------------------------------------------------------------------
  const PERFIL_PADRAO = { genero: "m", pele: "morena_clara", cabelo: "curto", cabelo_cor: "castanho_escuro", olhos_cor: "castanho",
    roupa: "camiseta", roupa_cor1: "azul", roupa_cor2: "branco", roupa_cor3: "marinho", traje: "", acessorios: [], escala: 1,
    rosto: "redondo", olhos_estilo: "normal", sobrancelha: "normal", nariz: "botao", bochechas: "rosadas" };
  const HEXRE = /^#[0-9A-Fa-f]{6}$/;

  function corDe(v, tabela, padrao) {
    if (typeof v === "string") {
      if (HEXRE.test(v)) return v.toUpperCase();
      for (const t of tabela) if (t[0] === v) return t[2];
    }
    return tabela.find((t) => t[0] === padrao)[2];
  }
  function normalizar(perfil, D) {
    const p = Object.assign({}, PERFIL_PADRAO);
    for (const k in perfil || {}) if (k in p) p[k] = perfil[k];
    p.genero = String(p.genero).toLowerCase().startsWith("f") ? "f" : "m";
    if (!(p.cabelo in D.cabelos)) p.cabelo = p.genero === "m" ? PERFIL_PADRAO.cabelo : "longo";
    if (!(p.roupa in D.roupas)) p.roupa = PERFIL_PADRAO.roupa;
    p.traje = p.traje in D.trajes ? p.traje : "";
    for (const opc of D.rosto_ordem) if (typeof p[opc] !== "string" || !(p[opc] in D.rosto.m[opc])) p[opc] = PERFIL_PADRAO[opc];
    const acs = Array.isArray(p.acessorios) ? p.acessorios : [];
    p.acessorios = acs.filter((a, i) => a in D.acessorios && acs.indexOf(a) === i);
    const e = parseFloat(p.escala);
    p.escala = isNaN(e) ? 1 : Math.max(0.6, Math.min(1.6, e));
    return p;
  }
  function paleta(p, traje, D) {
    const pal = Object.assign({}, D.paleta_fixa);
    pal.pele = corDe(p.pele, D.peles, "morena_clara");
    pal.cabelo = corDe(p.cabelo_cor, D.cores_cabelo, "castanho_escuro");
    pal.olhos = corDe(p.olhos_cor, D.cores_olhos, "castanho");
    pal.r1 = corDe(p.roupa_cor1, D.cores_roupa, "azul");
    pal.r2 = corDe(p.roupa_cor2, D.cores_roupa, "branco");
    pal.r3 = corDe(p.roupa_cor3, D.cores_roupa, "marinho");
    if (traje) Object.assign(pal, traje.cores || {});
    return pal;
  }
  function montarNo(molde, slots, pal, g) {
    const no = { id: molde.id, pos: (g === "f" && molde.pos_f ? molde.pos_f : molde.pos).slice() };
    for (const k of ["z", "seg", "mir", "inv", "contorno"]) if (molde[k]) no[k] = molde[k];
    const ss = molde.slot || [];
    const lista = [].concat(typeof ss === "string" ? [ss] : ss);
    const prims = [];
    for (const s of lista) for (const x of slots[s] || []) prims.push(x);
    no.prims = prims.map((x) => resolverPrim(x, pal));
    no.filhos = (molde.filhos || []).map((f) => montarNo(f, slots, pal, g));
    return no;
  }
  function montar(perfil, D) {
    const p = normalizar(perfil, D), g = p.genero;
    const traje = p.traje ? D.trajes[p.traje] : null;
    const pal = paleta(p, traje, D);
    const slots = clone(D.corpo[g]);
    const olhosTraje = (traje && traje.olhos) || "normal";
    for (const opc of D.rosto_ordem) {   // rosto escolhido (com fantasia: cabeça redonda, e olho da máscara se ela tiver)
      let val = traje && opc === "rosto" ? "redondo" : p[opc];
      if (opc === "olhos_estilo" && olhosTraje !== "normal") val = null;
      if (val) { const ss = D.rosto[g][opc][val].slots; for (const s in ss) slots[s] = clone(ss[s]); }
    }
    if (olhosTraje !== "normal") { const oe = D.olhos[g][olhosTraje]; for (const s in oe) slots[s] = clone(oe[s]); }
    const pecas = traje ? traje.pecas[g] : D.roupas[p.roupa].pecas[g];
    for (const s in pecas) (slots[s] = slots[s] || []).push(...clone(pecas[s]));
    const esconde = new Set((traje && traje.esconde) || []);
    let balanco = 0;
    if (!esconde.has("cabelo")) {
      const cab = D.cabelos[(traje && traje.forca_cabelo) || p.cabelo];
      slots.cabelo_tras = clone(cab.tras || []);
      slots.cabelo_frente = clone(cab.frente || []);
      balanco = cab.balanco == null ? 0.3 : cab.balanco;
    }
    for (const id of p.acessorios) {
      const pc = D.acessorios[id].pecas;
      for (const s in pc) {
        if (esconde.has(s) || (["acessorio", "mascara_cima", "mascara_baixo"].includes(s) && esconde.has("acessorio"))) continue;
        (slots[s] = slots[s] || []).push(...clone(pc[s]));
      }
    }
    for (const s of esconde) if (s === "sobr" || s === "boca") slots[s] = [];
    return { perfil: p, sombra: D.sombra.map((x) => resolverPrim(x, pal)), balanco, raiz: montarNo(D.rig, slots, pal, g) };
  }

  // ---- desenho -----------------------------------------------------------------------------------------
  const ALTURA_BASE = 224;
  function bboxD(d) {
    const t = d.split(" "); let i = 0; const xs = [], ys = [];
    const q = { M: 2, L: 2, Q: 4, C: 6, Z: 0 };
    while (i < t.length) { const c = t[i++]; const n = q[c]; for (let j = 0; j < n; j += 2) { xs.push(parseFloat(t[i + j])); ys.push(parseFloat(t[i + j + 1])); } i += n; }
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
  }
  function rrPath(x, y, w, h, r) {
    const p = new Path2D(); r = Math.min(r, w / 2, h / 2);
    p.moveTo(x + r, y); p.lineTo(x + w - r, y); p.arcTo(x + w, y, x + w, y + r, r); p.lineTo(x + w, y + h - r); p.arcTo(x + w, y + h, x + w - r, y + h, r);
    p.lineTo(x + r, y + h); p.arcTo(x, y + h, x, y + h - r, r); p.lineTo(x, y + r); p.arcTo(x, y, x + r, y, r); p.closePath(); return p;
  }
  function compPrim(p) {
    let path, caixa;
    if (p.t === "el") { path = new Path2D(); path.ellipse(p.x, p.y, p.rx, p.ry, 0, 0, PI2); caixa = [p.x - p.rx, p.y - p.ry, p.x + p.rx, p.y + p.ry]; }
    else if (p.t === "rr") { path = rrPath(p.x, p.y, p.w, p.h, p.r); caixa = [p.x, p.y, p.x + p.w, p.y + p.h]; }
    else { path = new Path2D(p.d); caixa = bboxD(p.d); }
    return { path, caixa, f: p.f, s: p.s, lw: p.lw || 0, o: p.o == null ? 1 : p.o, v: p.v, liga: p.liga, desl: p.desl, c: !!p.c };
  }
  function compNo(n) {
    const filhos = n.filhos.map(compNo);
    return { id: n.id, pos: n.pos, z: n.z || 0, seg: n.seg, mir: !!n.mir, inv: !!n.inv, contorno: !!n.contorno, prims: n.prims.map(compPrim), antes: filhos.filter((f) => f.z < 0), depois: filhos.filter((f) => f.z >= 0) };
  }
  function pincel(ctx, f, c) {
    if (!f) return null;
    if (typeof f === "string") return f;
    const cores = f.slice(1), x0 = c[0], y0 = c[1], x1 = c[2], y1 = c[3];
    let g;
    if (f[0] === "v") g = ctx.createLinearGradient(0, y0, 0, y1);
    else if (f[0] === "h") g = ctx.createLinearGradient(x0, 0, x1, 0);
    else g = ctx.createRadialGradient((x0 + x1) / 2, (y0 + y1) / 2, 0, (x0 + x1) / 2, (y0 + y1) / 2, Math.max(x1 - x0, y1 - y0) / 2);
    cores.forEach((cor, i) => g.addColorStop(cores.length > 1 ? i / (cores.length - 1) : 0, cor));
    return g;
  }
  class Desenhista {
    constructor(cena) { this.cena = cena; this.raiz = compNo(cena.raiz); this.sombra = cena.sombra.map(compPrim); }
    desenhar(ctx, pose) {
      const base = ctx.globalAlpha;
      ctx.save(); ctx.scale(pose["sombra.sx"] == null ? 1 : pose["sombra.sx"], 1);
      for (const pr of this.sombra) this._prim(ctx, pr, pose, base * (pose["sombra.o"] == null ? 1 : pose["sombra.o"]));
      ctx.restore();
      this._no(ctx, this.raiz, pose, base);
    }
    _no(ctx, no, pose, base, fase = 0) {
      // braço (nó com contorno): primeiro só os contornos do galho, depois o resto (o cotovelo fica sem emenda)
      if (fase === 0 && no.contorno) { this._no(ctx, no, pose, base, 1); this._no(ctx, no, pose, base, 2); return; }
      const g = (k, d) => (pose[no.id + k] == null ? d : pose[no.id + k]);
      let x = g(".x", 0), y = g(".y", 0), r = g(".r", 0), sx = g(".sx", 1), sy = g(".sy", 1);
      if (no.seg) {
        const h = (k, d) => (pose[no.seg + k] == null ? d : pose[no.seg + k]);
        x += h(".x", 0); y += h(".y", 0); r += h(".r", 0); sx *= h(".sx", 1); sy *= h(".sy", 1);
      }
      ctx.save();
      ctx.translate(no.pos[0] + x, no.pos[1] + y);
      if (r) ctx.rotate(((no.inv ? -r : r) * Math.PI) / 180);
      ctx.scale(no.mir ? -sx : sx, sy);
      for (const f of no.antes) this._no(ctx, f, pose, base, fase);
      for (const pr of no.prims) if (!fase || (fase === 1) === pr.c) this._prim(ctx, pr, pose, base);
      for (const f of no.depois) this._no(ctx, f, pose, base, fase);
      ctx.restore();
    }
    _prim(ctx, pr, pose, base) {
      if (pr.v != null && (pose["boca.v"] || "fechada") !== pr.v) return;
      let o = pr.o * base;
      if (pr.liga) o *= lim(pose[pr.liga] || 0);
      if (pr.desl) o *= 1 - lim(pose[pr.desl] || 0);
      if (o <= 0.004) return;
      ctx.globalAlpha = o;
      const fill = pincel(ctx, pr.f, pr.caixa);
      if (fill) { ctx.fillStyle = fill; ctx.fill(pr.path); }
      if (pr.s && pr.lw) { ctx.strokeStyle = pr.s; ctx.lineWidth = pr.lw; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.stroke(pr.path); }
      ctx.globalAlpha = base;
    }
  }

  // ---- animação ---------------------------------------------------------------------------------------
  class Aleatorio {
    constructor(s) { this.s = s >>> 0; }
    prox() {
      this.s = (this.s + 0x6D2B79F5) >>> 0;
      let t = this.s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    entre(a, b) { return a + (b - a) * this.prox(); }
    escolher(pares) {
      let total = 0; for (const p of pares) total += p[1];
      let x = this.prox() * total;
      for (const p of pares) { x -= p[1]; if (x < 0) return p[0]; }
      return pares[pares.length - 1][0];
    }
  }
  const padrao = (c) => (c.endsWith(".sx") || c.endsWith(".sy") || c === "sombra.o" ? 1 : 0);
  function tangente(k, i) {   // curva monotônica: 0 nos extremos e nas pontas (nunca passa do valor)
    if (i === 0 || i === k.length - 1) return 0;
    const h0 = k[i][0] - k[i - 1][0], h1 = k[i + 1][0] - k[i][0];
    if (h0 <= 0 || h1 <= 0) return 0;
    const d0 = (k[i][1] - k[i - 1][1]) / h0, d1 = (k[i + 1][1] - k[i][1]) / h1;
    if (d0 * d1 <= 0) return 0;
    const w1 = 2 * h1 + h0, w2 = h1 + 2 * h0;
    return (w1 + w2) / (w1 / d0 + w2 / d1);
  }
  function avaliar(spec, u) {
    if (spec.seno) { const [b, a, c, f] = spec.seno; return b + a * Math.sin(2 * Math.PI * (c * u + f)); }
    const k = spec.k;
    if (u <= k[0][0]) return k[0][1];
    for (let i = 0; i < k.length - 1; i++) {
      const [t0, v0] = k[i], [t1, v1] = k[i + 1];
      if (u <= t1) {
        const h = t1 - t0;
        if (h <= 0) return v1;
        const s = (u - t0) / h, s2 = s * s, s3 = s * s * s;
        return (2 * s3 - 3 * s2 + 1) * v0 + (s3 - 2 * s2 + s) * h * tangente(k, i) + (-2 * s3 + 3 * s2) * v1 + (s3 - s2) * h * tangente(k, i + 1);
      }
    }
    return k[k.length - 1][1];
  }
  function poseDoClipe(clipe, u) { const o = {}; for (const c in clipe.trilhas) o[c] = avaliar(clipe.trilhas[c], u); return o; }
  function somar(pose, extra) {
    for (const c in extra) { const v = extra[c]; if (c in pose) pose[c] = padrao(c) === 1 ? pose[c] * v : pose[c] + v; else pose[c] = v; }
  }
  function misturarPose(a, b, k) {
    const o = {}; const ks = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const c of ks) { const x = a[c] == null ? padrao(c) : a[c], y = b[c] == null ? padrao(c) : b[c]; o[c] = x + (y - x) * k; }
    return o;
  }
  function amplitudeFalsa(t, semente = 1.3) {
    const silaba = 0.5 + 0.5 * Math.sin(t * 12.5 + semente), envelope = 0.55 + 0.45 * Math.sin(t * 2.1 + semente * 1.7);
    const palavra = Math.sin(t * 1.6 + semente * 2.3) > -0.55 ? 1.0 : 0.08, tremor = 0.15 * Math.sin(t * 31 + semente * 3);
    return lim(Math.pow(silaba, 1.4) * envelope * palavra + tremor * palavra);
  }
  const TRANSICAO = 0.28, FADE_GESTO = 0.2;

  class Animador {
    constructor(A, arquetipo, expressaoParado, semente) {
      this.A = A;
      this.arqId = arquetipo in A.arquetipos ? arquetipo : A.arquetipo_padrao;
      this.arq = A.arquetipos[this.arqId];
      this.exprParado = expressaoParado in A.expressoes ? expressaoParado : null;
      this.rng = new Aleatorio(semente == null ? 1 : semente);
      this.estado = "idle"; this.tEstado = 0; this.movendo = 0; this.ritmo = 1; this.overlay = null;
      this.proxIdle = null; this.proxPiscar = null; this.piscando = null; this.olharAlvo = [0, 0];
      this.visemas = []; this.visema = "fechada"; this.tVisema = -9;
      this._t = null; this._amp = 0; this._ampAnt = 0; this._ampReal = 0; this._ampTs = -9;
      this._de = {}; this._tTroca = -9; this._ultima = {}; this._face = {}; this._look = [0, 0];
      this._ext = { ondas: 0, pensando: 0, zzz: 0, holo: 0, notas: 0 };
      this._mola = {}; this._mexendo = false; this._batida = null; this._batidaAte = 0; this.balanco = 1;
    }
    mudar(estado, agora) {
      if (!["idle", "ouvindo", "pensando", "falando", "descansando"].includes(estado)) estado = "idle";
      if (estado === this.estado) return;
      this._de = Object.fromEntries(Object.entries(this._ultima).filter((e) => typeof e[1] !== "string")); this._tTroca = agora; this.estado = estado; this.tEstado = agora; this.overlay = null; this.proxIdle = null;
      this._batida = null;
    }
    nivel(v, agora) { this._ampReal = lim(v); this._ampTs = agora; }
    texto(frase) {
      const s = []; for (const ch of (frase || "").toLowerCase()) {
        const v = this.A.vogais[ch];
        if (v) s.push(v); else if ("bmp".includes(ch) && s.length && s[s.length - 1] !== "M") s.push("M");
      }
      this.visemas = s;
    }
    gesto(nome, agora) {
      const c = this.A.clipes[nome]; if (!c || c.loop) return false;
      this.overlay = { nome, t0: agora, dur: c.dur / Math.max(0.3, this.arq.vel) }; return true;
    }
    andar(dir, ritmo = 1) { this.movendo = dir | 0; this.ritmo = ritmo; }
    olhar(dx, dy) { this.olharAlvo = [lim(dx, -1, 1), lim(dy, -1, 1)]; }
    ocupado() { return this.estado !== "idle" || this.overlay !== null; }
    fps(agora) {
      if (this.estado === "descansando") return 15;
      if (this.overlay || this.movendo || this.estado === "falando" || this.estado === "ouvindo" || agora - this._tTroca < TRANSICAO || this.piscando !== null || this._amp > 0.02 || this._mexendo) return 60;
      return 30;
    }
    quadro(agora) {
      const A = this.A, arq = this.arq, est = this.estado, vel = arq.vel;
      const dt = this._t === null ? 0 : lim(agora - this._t, 0, 0.2); this._t = agora;
      let [nomeBase, exprEst] = arq.estado[est];
      if (est === "idle" && this.movendo && arq.passeio.andar !== "flutua") nomeBase = "andar";
      const clipe = A.clipes[nomeBase];
      const ritmo = (nomeBase === "andar" ? this.ritmo : 1) * vel;
      const u = ((((agora - this.tEstado) * ritmo) / clipe.dur) % 1 + 1) % 1;
      let pose = poseDoClipe(clipe, u);
      const ampS = lim(this._amp);
      if (clipe.gesto) { const g = (0.3 + 0.7 * ampS) * arq.amp; for (const c in pose) pose[c] *= g; }
      if (nomeBase === "parado") somar(pose, arq.postura);
      if (est !== "descansando") for (const ex of arq.base) { const ce = A.clipes[ex]; somar(pose, poseDoClipe(ce, ((((agora - this.tEstado) * vel) / ce.dur) % 1 + 1) % 1)); }
      if (this.movendo && est === "idle") pose["raiz.r"] = (pose["raiz.r"] || 0) + 3.5 * this.movendo;
      if (this._tTroca + TRANSICAO > agora && Object.keys(this._de).length) pose = misturarPose(this._de, pose, suave((agora - this._tTroca) / TRANSICAO));

      let exprNome = exprEst, bocaLista = null, extrasGesto = [];
      if (est === "idle" && this.exprParado) exprNome = this.exprParado;
      let ov = this.overlay;
      if (ov) {
        const ce = A.clipes[ov.nome], dec = agora - ov.t0;
        if (dec >= ov.dur) { this.overlay = ov = null; this.proxIdle = null; }
        else {
          const w = suave(Math.min(1, dec / FADE_GESTO, (ov.dur - dec) / FADE_GESTO));
          const pc = poseDoClipe(ce, dec / ov.dur);
          for (const c in pc) {
            const d = padrao(c); const v = d + (pc[c] - d) * arq.amp; const at = pose[c] == null ? d : pose[c];
            pose[c] = at + (v - at) * w;
          }
          if (ce.expr) exprNome = ce.expr;
          bocaLista = ce.boca || null; extrasGesto = ce.extras || []; ov.u = dec / ov.dur;
        }
      }
      if (est === "idle" && !this.movendo && !this.overlay) {
        if (this.proxIdle === null) this.proxIdle = agora + this.rng.entre(arq.intervalo[0], arq.intervalo[1]);
        else if (agora >= this.proxIdle) { this.gesto(this.rng.escolher(arq.idle), agora); this.proxIdle = null; }
      }
      if (est === "falando" && arq.fala) {   // braços da fala: uma pose (batida) por trecho, com força pelo volume
        if (this._batida === null || agora >= this._batidaAte) {
          this._batida = A.poses_fala[this.rng.escolher(arq.fala)];
          this._batidaAte = agora + this.rng.entre(A.troca_fala[0], A.troca_fala[1]) / vel;
        }
        const g = (0.35 + 0.65 * ampS) * arq.amp, extra = {};
        for (const c in this._batida) extra[c] = this._batida[c] * g;
        somar(pose, extra);
      }
      if (est !== "descansando") for (const c in A.vida) {   // vida: balanço pequeno e contínuo
        const [a, hz, fase] = A.vida[c];
        pose[c] = (pose[c] || 0) + a * Math.sin(2 * Math.PI * (hz * agora + fase));
      }
      const alvo = A.expressoes[exprNome] || A.expressoes.neutro, f = this._face;
      const k = dt ? 1 - Math.exp(-dt / 0.10) : 1;
      for (const c of ["sobr_e", "sobr_d", "sobr_r", "aber", "feliz"]) f[c] = c in f ? f[c] + (alvo[c] - f[c]) * k : alvo[c];
      const seguir = (est === "idle" || est === "ouvindo") && !this.overlay;
      const ox = alvo.olhar[0] + (seguir ? this.olharAlvo[0] * 3.2 * arq.olhar_mouse : 0);
      const oy = alvo.olhar[1] + (seguir ? this.olharAlvo[1] * 2.6 * arq.olhar_mouse : 0);
      const kl = dt ? 1 - Math.exp(-dt / 0.14) : 1;
      this._look[0] += (ox - this._look[0]) * kl; this._look[1] += (oy - this._look[1]) * kl;
      this._piscar(agora);
      const aber = f.aber * (1 - 0.96 * this._curvaPiscar(agora)) * (1 - 0.96 * f.feliz);
      pose["abertura_e.sy"] = pose["abertura_d.sy"] = Math.max(0.03, aber);
      pose["olhos.fechado"] = lim((0.42 - aber) / 0.3) * (1 - lim(f.feliz));
      pose["olhos.oculto"] = 1 - lim((aber - 0.10) / 0.2);
      pose["olhos.feliz"] = lim(f.feliz);
      for (const [lado, sinal] of [["e", 1], ["d", -1]]) {
        pose["sobr_" + lado + ".y"] = f["sobr_" + lado]; pose["sobr_" + lado + ".r"] = f.sobr_r * sinal;
        pose["iris_" + lado + ".x"] = (pose["iris_" + lado + ".x"] || 0) + this._look[0];
        pose["iris_" + lado + ".y"] = (pose["iris_" + lado + ".y"] || 0) + this._look[1];
      }
      if (seguir) {
        pose["cabeca.x"] = (pose["cabeca.x"] || 0) + this.olharAlvo[0] * 1.6 * arq.olhar_mouse;
        pose["cabeca.r"] = (pose["cabeca.r"] || 0) + this.olharAlvo[0] * 2.4 * arq.olhar_mouse;
      }
      this._molas(pose, dt);
      const bv = this._boca(agora, dt, alvo.boca, bocaLista, ov);
      pose["boca.v"] = bv[0]; pose["boca.sy"] = bv[1];
      const e = this._ext;
      const eAlvo = { ondas: est === "ouvindo" || est === "falando" ? 1 : 0, pensando: est === "pensando" ? 1 : 0, zzz: est === "descansando" ? 1 : 0,
        holo: extrasGesto.includes("holo") || (clipe.extras || []).includes("holo") ? 1 : 0, notas: extrasGesto.includes("notas") ? 1 : 0 };
      for (const c in eAlvo) e[c] += (eAlvo[c] - e[c]) * (dt ? 1 - Math.exp(-dt / 0.15) : 1);
      const ex = {}; for (const c in e) ex[c] = Math.round(e[c] * 1000) / 1000;
      ex.amp = Math.round(this._amp * 1000) / 1000; ex.aura = arq.aura;
      this._ultima = pose;
      return { pose, extras: ex, estado: est, gesto: this.overlay ? this.overlay.nome : "", arquetipo: this.arqId };
    }
    _molas(pose, dt) {   // inércia: cada canal persegue a pose como uma mola; capa e cabelo ficam para trás
      const A = this.A, alvo = {};
      for (const c in A.molas) alvo[c] = pose[c] == null ? 0 : pose[c];
      for (const c in A.inercia) {
        const [fator, canais, passo, limite] = A.inercia[c], k = c === "cabelo_tras.r" ? this.balanco : 1;
        let giro = 0; for (const x of canais) giro += pose[x] == null ? 0 : pose[x];
        alvo[c] += lim((fator * giro + passo * this.movendo) * k, -limite, limite);
      }
      const n = dt > 0 ? Math.max(1, Math.ceil(dt * 240 - 1e-9)) : 0, h = n ? dt / n : 0;
      let mexendo = false;
      for (const c in A.molas) {
        const [hz, zeta] = A.molas[c];
        let m = this._mola[c];
        if (m === undefined) m = this._mola[c] = [alvo[c], 0];
        else if (n) {
          const w = 2 * Math.PI * hz; let x = m[0], v = m[1];
          for (let i = 0; i < n; i++) { v += (w * w * (alvo[c] - x) - 2 * zeta * w * v) * h; x += v * h; }
          m[0] = x; m[1] = v;
        }
        pose[c] = m[0];
        mexendo = mexendo || Math.abs(m[1]) > 2 || Math.abs(m[0] - alvo[c]) > 0.3;
      }
      this._mexendo = mexendo;
    }
    _piscar(agora) {
      if (this.piscando !== null && agora - this.piscando >= 0.16) this.piscando = null;
      if (this.proxPiscar === null) this.proxPiscar = agora + this.rng.entre(this.arq.piscar[0], this.arq.piscar[1]);
      else if (this.piscando === null && agora >= this.proxPiscar) {
        this.piscando = agora; const dupla = this.rng.prox() < 0.15;
        this.proxPiscar = agora + (dupla ? 0.3 : this.rng.entre(this.arq.piscar[0], this.arq.piscar[1]));
      }
    }
    _curvaPiscar(agora) {
      if (this.piscando === null) return 0;
      const u = (agora - this.piscando) / 0.16; return u < 0.5 ? suave(u * 2) : suave(2 - u * 2);
    }
    _boca(agora, dt, repouso, lista, ov) {
      if (this.estado === "falando") {
        const alvo = agora - this._ampTs < 0.3 ? this._ampReal : amplitudeFalsa(agora);
        this._amp += (alvo - this._amp) * (1 - Math.pow(0.65, dt * 60));
      } else this._amp *= Math.pow(0.5, dt * 30);
      const a = this._amp;
      if (this.estado === "falando") {
        if (a > 0.16 && a - this._ampAnt > 0.035 && agora - this.tVisema > 0.075) {
          const seq = this.A.sequencia_visemas;
          this.visema = this.visemas.length ? this.visemas.shift() : seq[Math.floor(this.rng.prox() * seq.length)];
          this.tVisema = agora;
        }
        this._ampAnt = a;
        if (a < 0.09) return [repouso !== "fechada" ? repouso : "sorriso", 1];
        return [this.visema, 0.72 + 0.55 * a];
      }
      this._ampAnt = a;
      if (lista && ov) { let v = repouso; for (const [t, nome] of lista) if ((ov.u || 0) >= t) v = nome; return [v, 1]; }
      return [repouso, 1];
    }
  }

  // ---- passeio -----------------------------------------------------------------------------------------------
  class Passeio {
    constructor(modo, alcance, vel, pausa, semente = 5) {
      this.modo = ["fixo", "curto", "tela", "livre"].includes(modo) ? modo : "fixo";
      this.alcance = alcance; this.vel = vel; this.pausa = pausa; this.rng = new Aleatorio(semente);
      this.origem = null; this.alvo = null; this.inicio = null; this.dur = 0; this.esperaAte = null; this.direcao = 0;
    }
    novoLugar(x, y) { this.origem = [x, y]; this.alvo = null; this.inicio = null; this.direcao = 0; this.esperaAte = null; }
    _escolher(x, y, area, larg) {
      const [esq, topo, dir, baixo] = area, [ox, oy] = this.origem, r = this.rng;
      if (this.modo === "curto") { const lo = Math.max(esq, ox - this.alcance), hi = Math.min(dir - larg, ox + this.alcance); return [r.entre(lo, Math.max(lo, hi)), oy]; }
      if (this.modo === "tela") return [r.entre(esq, Math.max(esq, dir - larg)), oy];
      const al = Math.max(0, (baixo - topo) * 0.55);
      return [r.entre(esq, Math.max(esq, dir - larg)), r.entre(oy - al, oy)];
    }
    atualizar(agora, x, y, area, ocupado, larg = 120) {
      if (this.origem === null) this.origem = [x, y];
      if (this.modo === "fixo" || ocupado) {
        if (ocupado && this.alvo) { this.origem = [x, y]; this.alvo = null; this.inicio = null; }
        this.direcao = 0; if (ocupado) this.esperaAte = null; return [x, y, 0];
      }
      if (this.alvo === null) {
        if (this.esperaAte === null) this.esperaAte = agora + this.rng.entre(this.pausa[0], this.pausa[1]);
        if (agora < this.esperaAte) return [x, y, 0];
        const alvo = this._escolher(x, y, area, larg);
        const dist = Math.hypot(alvo[0] - x, alvo[1] - y);
        if (dist < 40) { this.esperaAte = agora + this.rng.entre(this.pausa[0], this.pausa[1]) * 0.5; return [x, y, 0]; }
        this.alvo = alvo; this.inicio = [x, y, agora]; this.dur = Math.max(0.8, dist / this.vel); this.esperaAte = null;
      }
      const [x0, y0, t0] = this.inicio, u = (agora - t0) / this.dur;
      if (u >= 1) { const r = [this.alvo[0], this.alvo[1], 0]; this.alvo = this.inicio = null; this.direcao = 0; return r; }
      const k = suave(u); let nx = x0 + (this.alvo[0] - x0) * k, ny = y0 + (this.alvo[1] - y0) * k;
      this.direcao = this.alvo[0] > x0 ? 1 : this.alvo[0] < x0 ? -1 : 0;
      nx = Math.min(Math.max(nx, area[0]), Math.max(area[0], area[2] - larg)); ny = Math.min(Math.max(ny, area[1]), area[3]);
      return [nx, ny, this.direcao];
    }
  }

  raiz.Personagem = { montar, normalizar, Desenhista, Animador, Aleatorio, Passeio, misturar, resolverCor, ALTURA_BASE, PERFIL_PADRAO, amplitudeFalsa };
})(typeof window !== "undefined" ? window : globalThis);
