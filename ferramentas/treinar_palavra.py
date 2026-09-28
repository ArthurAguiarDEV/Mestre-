"""Treina o detector local da palavra de ativacao (ex.: "Assessor") NESTE PC, gratis.

Uso (da pasta do projeto):  venv\\Scripts\\python ferramentas\\treinar_palavra.py [opcoes]
Ou pelo ferramentas\\15_treinar_palavra.bat (pergunta se quer gravar a sua voz).

O que ele faz:
 1. Baixa (uma vez, ~2,4 MB) os dois modelos de caracteristicas do openWakeWord v0.5.1 (Apache-2.0):
    melspectrogram.onnx e embedding_model.onnx -> modelos/palavra/
 2. POSITIVOS: a palavra falada por vozes sinteticas locais (Kokoro, misturando as 3 vozes em portugues
    em proporcoes sorteadas + um pouco de outras vozes, velocidade 0,75-1,3x), vozes Edge em pt-BR/pt-PT
    (internet, opcional) e as SUAS gravacoes (--gravar-minha-voz N, ficam em modelos/palavra/amostras/).
 3. NEGATIVOS: palavras parecidas ("acessar", "sucessor", "professor"...), frases do memoria/ouvido.jsonl
    sem a palavra (o que o microfone ja ouviu de video/conversa) faladas pelas vozes, os audios reais em
    logs/ sem a palavra, gravacao do ambiente (--gravar-ambiente MIN: deixe um video tocando) e ruido.
 4. Mistura fundo/ruido/eco nos positivos, calcula as caracteristicas com a MESMA classe do detector
    ao vivo (app/palavra_local.Caracteristicas) e treina uma rede pequena (torch, processador).
 5. Mede acerto e disparos falsos por hora (inclusive nas suas gravacoes reais, se houver) e grava
    modelos/palavra/<palavra>.npz. Depois: painel > Audio > "Detector local da palavra".
"""
import argparse
import json
import random
import sys
import time
import urllib.request
import wave
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJETO))

import numpy as np  # noqa: E402

from app import palavra_local as pl  # noqa: E402
from app.config import carregar_config, palavras_ativacao  # noqa: E402
from app.texto import normalizar, parecida  # noqa: E402

TAXA = 16000
URL_CARAC = "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/"
PASTA = PROJETO / pl.PASTA
AMOSTRAS = PASTA / "amostras"
PARECIDAS = ["acessar", "acesso", "acessou", "sucessor", "sucesso", "professor", "processo", "processador",
             "sessão", "assim sei", "a ser", "assessoria", "assistir", "assistente", "agressor", "ascensor",
             "é sério", "a sessão", "o sucessor", "acessório", "assessorar", "cessar", "o professor", "possessão",
             "acessível", "vai ser", "a senhora", "assim assim", "confessor", "compressor"]
FRASES_POS = ["{P}.", "{P}!", "{P}?", "Ô {P}.", "Ei {P}.", "E aí {P}.", "Fala {P}.", "Oi {P}.", "Bom dia {P}.",
              "Então {P}.", "Ô {P}!", "Olha {P}."]
VOZES_EDGE = ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-BR-ThalitaMultilingualNeural",
              "pt-PT-DuarteNeural", "pt-PT-RaquelNeural"]


def dizer(*a):
    print(*a, flush=True)


# --- 1) modelos de caracteristicas --------------------------------------------------------------
def baixar_caracteristicas() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    for nome in (pl.MEL, pl.EMBEDDING):
        destino = PASTA / nome
        if destino.exists():
            continue
        dizer(f"Baixando {nome} (openWakeWord, Apache-2.0)...")
        with urllib.request.urlopen(URL_CARAC + nome, timeout=60) as r:
            dados = r.read()
        destino.write_bytes(dados)


# --- audio util ----------------------------------------------------------------------------------
def ler_wav(caminho: Path) -> np.ndarray | None:
    """float32 -1..1 a 16 kHz (mono)."""
    try:
        with wave.open(str(caminho)) as w:
            taxa, canais, n = w.getframerate(), w.getnchannels(), w.getnframes()
            a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
        if canais > 1:
            a = a.reshape(-1, canais).mean(1)
        return reamostrar(a, taxa)
    except Exception:
        return None


def reamostrar(a: np.ndarray, taxa: int) -> np.ndarray:
    if taxa == TAXA:
        return a.astype(np.float32)
    from math import gcd

    from scipy.signal import resample_poly

    g = gcd(taxa, TAXA)
    return resample_poly(a, TAXA // g, taxa // g).astype(np.float32)


def aparar(a: np.ndarray, margem: float = 0.05) -> np.ndarray:
    """Tira o silencio do comeco e do fim (deixa `margem` s)."""
    if not len(a):
        return a
    env = np.convolve(np.abs(a), np.ones(160) / 160, "same")
    fortes = np.where(env > max(0.02 * env.max(), 1e-4))[0]
    if not len(fortes):
        return a
    m = int(margem * TAXA)
    return a[max(0, fortes[0] - m): fortes[-1] + m]


def salvar_wav(a: np.ndarray, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


# --- 2) vozes --------------------------------------------------------------------------------------
class Kokoro:
    def __init__(self):
        from app import voz_kokoro

        if not voz_kokoro.pronto():
            raise RuntimeError("voz Kokoro não instalada (painel > Voz > Kokoro > Baixar)")
        self.k = voz_kokoro._carregar()
        todas = list(self.k.get_voices())
        self.pt = [self.k.get_voice_style(v) for v in ("pm_alex", "pf_dora", "pm_santa")]
        self.outras = [v for v in todas if v not in ("pm_alex", "pf_dora", "pm_santa")]

    def falar(self, texto: str, rng: random.Random) -> np.ndarray:
        pesos = np.random.default_rng(rng.randrange(1 << 30)).dirichlet([0.7, 0.7, 0.7])
        estilo = sum(p * e for p, e in zip(pesos, self.pt))
        if self.outras and rng.random() < 0.5:   # um pouco de outro timbre (mais variedade de "pessoas")
            mistura = rng.uniform(0.1, 0.35)
            estilo = (1 - mistura) * estilo + mistura * self.k.get_voice_style(rng.choice(self.outras))
        audio, taxa = self.k.create(texto, voice=estilo, speed=rng.uniform(0.75, 1.3), lang="pt-br")
        return reamostrar(np.asarray(audio, np.float32), taxa)


def edge_falar(texto: str, rng: random.Random) -> np.ndarray | None:
    """Voz Edge (precisa de internet). None se falhar."""
    import asyncio
    import tempfile

    try:
        import edge_tts
        from faster_whisper import decode_audio
    except ImportError:
        return None
    arq = Path(tempfile.gettempdir()) / f"mestre_palavra_{rng.randrange(1 << 30)}.mp3"
    try:
        c = edge_tts.Communicate(texto, rng.choice(VOZES_EDGE), rate=f"{rng.randint(-20, 25):+d}%",
                                 pitch=f"{rng.randint(-12, 12):+d}Hz")
        asyncio.run(c.save(str(arq)))
        return decode_audio(str(arq), sampling_rate=TAXA).astype(np.float32)
    except Exception:
        return None
    finally:
        arq.unlink(missing_ok=True)


def gravar(segundos: float, aviso: str = "") -> np.ndarray:
    import sounddevice as sd

    if aviso:
        dizer(aviso)
    a = sd.rec(int(segundos * TAXA), samplerate=TAXA, channels=1, dtype="float32")
    sd.wait()
    return a.reshape(-1)


# --- 3) dados reais do projeto ----------------------------------------------------------------------
def audios_reais(alvos: list[str]) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """(com a palavra, sem a palavra): wavs de logs/ cujo texto transcrito e conhecido."""
    textos: dict[Path, str] = {}
    lista = PROJETO / "logs" / "audios" / "transcricoes.txt"
    if lista.exists():
        for linha in lista.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "  ->  " in linha:
                nome, texto = linha.split("  ->  ", 1)
                textos[PROJETO / "logs" / "audios" / nome.strip()] = texto.strip("'\" ")
    ouvido = PROJETO / "memoria" / "ouvido.jsonl"
    if ouvido.exists():
        for linha in ouvido.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                r = json.loads(linha)
            except ValueError:
                continue
            if r.get("audio") and r.get("texto"):
                textos[PROJETO / str(r["audio"])] = str(r["texto"])
    com, sem = [], []
    for caminho, texto in textos.items():
        if not caminho.exists():
            continue
        a = ler_wav(caminho)
        if a is None or len(a) < TAXA // 2:
            continue
        tem = any(parecida(p, alvos) for p in normalizar(texto).split())
        (com if tem else sem).append(a)
    return com, sem


def frases_sem_palavra(alvos: list[str], limite: int) -> list[str]:
    ouvido = PROJETO / "memoria" / "ouvido.jsonl"
    frases = []
    if ouvido.exists():
        for linha in ouvido.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                t = str(json.loads(linha).get("texto") or "")
            except ValueError:
                continue
            if 3 <= len(t.split()) <= 30 and not any(parecida(p, alvos) for p in normalizar(t).split()):
                frases.append(t)
    frases = list(dict.fromkeys(frases))
    random.Random(1).shuffle(frases)
    return frases[:limite]


def ruidos(rng: np.random.Generator, segundos: float = 120) -> list[np.ndarray]:
    n = int(segundos * TAXA / 3)
    branco = rng.normal(0, 1, n)
    rosa = np.cumsum(rng.normal(0, 1, n)) * 0.02
    rosa -= np.convolve(rosa, np.ones(400) / 400, "same")
    marrom = np.cumsum(rng.normal(0, 1, n))
    marrom -= np.convolve(marrom, np.ones(2000) / 2000, "same")
    return [(x / (np.abs(x).max() + 1e-9) * rng.uniform(0.02, 0.2)).astype(np.float32) for x in (branco, rosa, marrom)]


# --- 4) mistura e caracteristicas --------------------------------------------------------------------
def eco(a: np.ndarray, rng: random.Random) -> np.ndarray:
    dur = rng.uniform(0.08, 0.4)
    t = np.arange(int(dur * TAXA)) / TAXA
    ir = np.random.default_rng(rng.randrange(1 << 30)).normal(0, 1, len(t)) * np.exp(-t * 6.9 / dur)
    ir[0] = 1.0
    from scipy.signal import fftconvolve

    s = fftconvolve(a, ir / np.abs(ir).sum() * 3)[: len(a)]
    return (s / (np.abs(s).max() + 1e-9) * np.abs(a).max()).astype(np.float32)


def trecho(fundo: list[np.ndarray], n: int, rng: random.Random) -> np.ndarray:
    f = rng.choice(fundo)
    if len(f) < n:
        f = np.tile(f, n // max(1, len(f)) + 1)
    i = rng.randrange(0, len(f) - n + 1)
    return f[i:i + n]


def montar_positivo(palavra: np.ndarray, fundo: list[np.ndarray], rng: random.Random) -> tuple[np.ndarray, int]:
    """[fundo 1,0-1,6 s][palavra + fundo][cauda 0,1-0,4 s] -> (audio, amostra onde a palavra termina)."""
    p = aparar(palavra)
    if rng.random() < 0.35:
        p = eco(p, rng)
    p = p / (np.abs(p).max() + 1e-9) * rng.uniform(0.15, 0.95)
    antes, cauda = int(rng.uniform(1.0, 1.6) * TAXA), int(rng.uniform(0.1, 0.4) * TAXA)
    total = antes + len(p) + cauda
    fundo_a = trecho(fundo, total, rng)
    snr = rng.uniform(3, 30)
    rms_p = np.sqrt(np.mean(p ** 2)) + 1e-9
    rms_f = np.sqrt(np.mean(fundo_a ** 2)) + 1e-9
    audio = fundo_a * (rms_p / rms_f) / (10 ** (snr / 20))
    audio[antes:antes + len(p)] += p
    return np.clip(audio, -1, 1).astype(np.float32), antes + len(p)


def janelas_do_audio(carac: "pl.Caracteristicas", a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Passa o audio como ao vivo (blocos de 0,1 s). -> (janelas (k,16,96), amostra onde cada uma termina)."""
    carac.reiniciar()
    i16 = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    janelas, fins, feitos = [], [], 0
    for i in range(0, len(i16), 1600):
        novos = carac.adicionar(i16[i:i + 1600])
        for k in range(novos - 1, -1, -1):
            feitos += 1
            j = carac.ultimas(pl.JANELA_EMB, k)
            if j is not None:
                janelas.append(j[0])
                fins.append(feitos * pl.QUADRO)
    if not janelas:
        return np.zeros((0, pl.JANELA_EMB, 96), np.float32), np.zeros(0, int)
    return np.stack(janelas), np.array(fins)


def janelas_positivas(carac, audio, fim_palavra) -> tuple[np.ndarray, np.ndarray]:
    """Positivas: janelas que terminam ate 0,45 s depois da palavra. Negativas: as que terminam antes dela."""
    j, fins = janelas_do_audio(carac, audio)
    pos = (fins >= fim_palavra - 0.05 * TAXA) & (fins <= fim_palavra + 0.45 * TAXA)
    antes = fins < fim_palavra - 1.0 * TAXA   # (so fundo, sem a palavra ainda)
    return j[pos], j[antes]


# --- 5) rede ----------------------------------------------------------------------------------------
def treinar_rede(xp, xn, epocas: int, seed: int = 0) -> dict:
    import torch

    torch.manual_seed(seed)
    x = np.concatenate([xp, xn]).reshape(len(xp) + len(xn), -1)
    y = np.concatenate([np.ones(len(xp)), np.zeros(len(xn))]).astype(np.float32)
    media, desvio = x.mean(0), x.std(0) + 1e-4
    xt = torch.tensor((x - media) / desvio, dtype=torch.float32)
    yt = torch.tensor(y)
    rede = torch.nn.Sequential(torch.nn.Linear(xt.shape[1], 64), torch.nn.ReLU(), torch.nn.Dropout(0.3),
                               torch.nn.Linear(64, 32), torch.nn.ReLU(), torch.nn.Linear(32, 1))
    opt = torch.optim.AdamW(rede.parameters(), lr=1e-3, weight_decay=1e-3)
    peso_pos = torch.tensor(max(1.0, len(xn) / max(1, len(xp)) / 4))   # negativos sao muitos: pesa os positivos
    perda_f = torch.nn.BCEWithLogitsLoss(pos_weight=peso_pos)
    for ep in range(epocas):
        rede.train()
        ordem = torch.randperm(len(xt))
        total = 0.0
        for i in range(0, len(ordem), 256):
            idx = ordem[i:i + 256]
            opt.zero_grad()
            perda = perda_f(rede(xt[idx]).squeeze(1), yt[idx])
            perda.backward()
            opt.step()
            total += float(perda.detach()) * len(idx)
        if ep % 5 == 4 or ep == epocas - 1:
            dizer(f"   época {ep + 1}/{epocas}: perda {total / len(xt):.4f}")
    rede.eval()
    lin = [m for m in rede if isinstance(m, torch.nn.Linear)]
    pesos = {"media": media.astype(np.float32), "desvio": desvio.astype(np.float32), "n": np.array(pl.JANELA_EMB)}
    for i, m in enumerate(lin, 1):
        pesos[f"w{i}"] = m.weight.detach().numpy().T.astype(np.float32)
        pesos[f"b{i}"] = m.bias.detach().numpy().astype(np.float32)
    return pesos


def disparos(notas: np.ndarray, limiar: float) -> int:
    """Conta disparos (varias janelas seguidas acima do limiar = 1 disparo)."""
    acima = notas >= limiar
    return int(np.sum(acima[1:] & ~acima[:-1]) + (1 if len(acima) and acima[0] else 0))


def main() -> None:
    ap = argparse.ArgumentParser(description="Treina o detector local da palavra de ativação")
    ap.add_argument("--positivos", type=int, default=1500, help="falas sintéticas da palavra (Kokoro)")
    ap.add_argument("--edge", type=int, default=300, help="falas da palavra pelas vozes Edge (internet; 0 = não)")
    ap.add_argument("--negativos", type=int, default=800, help="frases/palavras parecidas faladas (sem a palavra)")
    ap.add_argument("--aumentos", type=int, default=3, help="cópias com fundo/eco diferentes de cada positivo")
    ap.add_argument("--gravar-minha-voz", type=int, default=0, help="grava N vezes você falando a palavra")
    ap.add_argument("--gravar-ambiente", type=float, default=0, help="grava N minutos do ambiente (vídeo tocando)")
    ap.add_argument("--epocas", type=int, default=30)
    ap.add_argument("--rapido", action="store_true", help="teste rápido (poucas amostras, modelo fraco)")
    ap.add_argument("--saida", default="", help="arquivo .npz (padrão: modelos/palavra/<palavra>.npz)")
    args = ap.parse_args()
    if args.rapido:
        args.positivos, args.edge, args.negativos, args.aumentos, args.epocas = 60, 0, 40, 2, 10

    inicio = time.time()
    cfg = carregar_config()
    alvos = palavras_ativacao(cfg)
    palavra = alvos[0].capitalize()
    saida = Path(args.saida) if args.saida else PASTA / pl.nome_arquivo(palavra)
    rng = random.Random(42)
    dizer(f"== Treino do detector da palavra “{palavra}” -> {saida}")

    baixar_caracteristicas()
    carac = pl.Caracteristicas(PASTA, threads=2)

    # gravacoes do dono / ambiente (ficam guardadas para os proximos treinos)
    AMOSTRAS.mkdir(parents=True, exist_ok=True)
    if args.gravar_minha_voz:
        dizer(f"\nVamos gravar você falando “{palavra}” {args.gravar_minha_voz} vezes (2 s cada).")
        dizer("Varie: normal, baixo, alto, rápido, de longe do microfone, com 'ô'/'e aí' antes...")
        for i in range(args.gravar_minha_voz):
            input(f"  [{i + 1}/{args.gravar_minha_voz}] Aperte ENTER e fale “{palavra}”...")
            a = gravar(2.0)
            salvar_wav(a, AMOSTRAS / f"dono_{time.strftime('%Y%m%d_%H%M%S')}_{i:02d}.wav")
    if args.gravar_ambiente:
        dizer(f"\nGravando {args.gravar_ambiente:.0f} min do ambiente. Deixe um vídeo/música tocando e NÃO fale "
              f"“{palavra}”...")
        a = gravar(args.gravar_ambiente * 60)
        salvar_wav(a, AMOSTRAS / f"ambiente_{time.strftime('%Y%m%d_%H%M%S')}.wav")

    # --- negativos ---
    dizer("\n[1/4] Juntando negativos (sem a palavra)...")
    t = time.time()
    real_com, real_sem = audios_reais(alvos)
    ambiente = [x for x in (ler_wav(f) for f in sorted(AMOSTRAS.glob("ambiente_*.wav"))) if x is not None]
    ruido = ruidos(np.random.default_rng(7))
    kokoro = Kokoro()
    textos_neg = PARECIDAS * 3 + frases_sem_palavra(alvos, args.negativos)
    rng.shuffle(textos_neg)
    fala_neg = []
    for i, texto in enumerate(textos_neg[:args.negativos]):
        try:
            fala_neg.append(kokoro.falar(texto, rng))
        except Exception:
            pass
        if i % 100 == 99:
            dizer(f"   {i + 1} negativos falados...")
    fundo = ruido + ambiente + real_sem + fala_neg
    dizer(f"   {len(fala_neg)} falas sintéticas, {len(real_sem)} áudios reais seus sem a palavra, "
          f"{len(ambiente)} gravação(ões) do ambiente, {len(ruido)} ruídos ({time.time() - t:.0f}s)")

    # --- positivos ---
    dizer("\n[2/4] Gerando a palavra com vozes diferentes...")
    t = time.time()
    falas_pos = []
    for i in range(args.positivos):
        texto = rng.choice(FRASES_POS).format(P=palavra)
        try:
            falas_pos.append(("kokoro", kokoro.falar(texto, rng)))
        except Exception:
            pass
        if i % 250 == 249:
            dizer(f"   {i + 1}/{args.positivos} (Kokoro)...")
    feitos_edge = 0
    for i in range(args.edge):
        a = edge_falar(rng.choice(FRASES_POS).format(P=palavra), rng)
        if a is None:
            if i == 0:
                dizer("   Vozes Edge indisponíveis (sem internet?): seguindo só com as locais.")
                break
            continue
        falas_pos.append(("edge", a))
        feitos_edge += 1
    dono = [x for x in (ler_wav(f) for f in sorted(AMOSTRAS.glob("dono_*.wav"))) if x is not None]
    falas_pos += [("dono", x) for x in dono for _ in range(10)]   # (a sua voz vale mais: 10 cópias com fundos diferentes)
    dizer(f"   {args.positivos} Kokoro + {feitos_edge} Edge + {len(dono)} gravações suas ({time.time() - t:.0f}s)")

    # --- caracteristicas ---
    dizer("\n[3/4] Calculando as características (igual ao detector ao vivo)...")
    t = time.time()
    rng.shuffle(falas_pos)
    corte = int(len(falas_pos) * 0.85)
    xp_tr, xp_va, xn_extra = [], [], []
    for i, (_, fala) in enumerate(falas_pos):
        for _ in range(args.aumentos if i < corte else 1):
            audio, fim = montar_positivo(fala, fundo, rng)
            pos, neg = janelas_positivas(carac, audio, fim)
            (xp_tr if i < corte else xp_va).append(pos)
            xn_extra.append(neg[::3])
        if i % 500 == 499:
            dizer(f"   {i + 1}/{len(falas_pos)} positivos...")
    # negativos em "fluxo": cada fonte vira um audio longo; 15% final de cada uma fica para a validacao
    xn_tr, xn_va, horas_va = [], [], 0.0
    for fonte in (fala_neg, real_sem, ambiente, ruido):
        if not fonte:
            continue
        longo = np.concatenate([np.concatenate([x, np.zeros(int(0.3 * TAXA), np.float32)]) for x in fonte])
        c = int(len(longo) * 0.85)
        j_tr, _ = janelas_do_audio(carac, longo[:c])
        j_va, _ = janelas_do_audio(carac, longo[c:])
        xn_tr.append(j_tr[::2])
        xn_va.append(j_va)
        horas_va += (len(longo) - c) / TAXA / 3600
    xp_tr, xp_va = np.concatenate(xp_tr), np.concatenate(xp_va)
    xn_tr = np.concatenate(xn_tr + xn_extra)
    xn_va = np.concatenate(xn_va)
    dizer(f"   positivas {len(xp_tr)} (+{len(xp_va)} validação), negativas {len(xn_tr)} "
          f"(+{len(xn_va)} validação = {horas_va * 60:.1f} min) ({time.time() - t:.0f}s)")

    # --- treino ---
    dizer("\n[4/4] Treinando a rede...")
    t = time.time()
    pesos = treinar_rede(xp_tr, xn_tr, args.epocas)
    rede = pl.Classificador(pesos)
    dizer(f"   treino: {time.time() - t:.0f}s")

    # --- avaliacao ---
    dizer("\n== Resultado (dados que o treino NÃO viu)")
    n_pos_va = len(xp_va)
    notas_pos = rede.notas(xp_va) if n_pos_va else np.zeros(0)
    notas_neg = rede.notas(xn_va) if len(xn_va) else np.zeros(0)
    for limiar in (0.3, 0.5, 0.7):
        acerto = float(np.mean(notas_pos >= limiar)) if n_pos_va else 0.0
        fa = disparos(notas_neg, limiar) / horas_va if horas_va else 0.0
        dizer(f"   exigência {limiar:.1f}: reconhece {acerto * 100:.0f}% das janelas com a palavra, "
              f"{fa:.1f} disparos falsos por hora (sintético)")
    reais = {}
    if real_com or real_sem:
        det_notas = lambda a: rede.notas(janelas_do_audio(carac, np.concatenate([np.zeros(TAXA, np.float32), a,  # noqa: E731
                                                                                  np.zeros(TAXA, np.float32)]))[0])
        for limiar in (0.3, 0.5, 0.7):
            ach = [float(det_notas(a).max(initial=0)) >= limiar for a in real_com]
            falsos = [float(det_notas(a).max(initial=0)) >= limiar for a in real_sem]
            reais[limiar] = (sum(ach), len(ach), sum(falsos), len(falsos))
            dizer(f"   exigência {limiar:.1f}, SUAS gravações reais: achou em {sum(ach)}/{len(ach)} com a palavra, "
                  f"disparou em {sum(falsos)}/{len(falsos)} sem a palavra")
    saida.parent.mkdir(parents=True, exist_ok=True)
    pesos["palavra"] = np.array(palavra)
    np.savez(saida, **pesos)
    relatorio = {"palavra": palavra, "quando": time.strftime("%Y-%m-%d %H:%M"), "minutos": round((time.time() - inicio) / 60, 1),
                 "positivos": len(falas_pos), "gravacoes_dono": len(dono), "reais": {str(k): v for k, v in reais.items()}}
    saida.with_suffix(".json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
    dizer(f"\nPronto em {(time.time() - inicio) / 60:.1f} min: {saida}")
    dizer("Agora: painel > Áudio > “Detector local da palavra” (ligar) > Salvar. Se ele não te ouvir, baixe a "
          "exigência ou treine de novo com mais gravações suas (--gravar-minha-voz 30).")


if __name__ == "__main__":
    main()
