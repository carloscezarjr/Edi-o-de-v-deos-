"""Monta o vídeo editado: legenda, gancho, animações, sons e chamada final.
Uso: python3 motor.py <pasta_video> <t0> <t1|fim> <saida.mp4>
"""
import json, math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/tmp/claude-0/-home-user-Edi-o-de-v-deos-/1ea065e1-57cf-5cb7-8257-961422c1fd55/scratchpad')
from estilo import anton, mont, legenda_impacto, gancho_manchete, ACC, W, H

FPS = 30
EXTRA_FIM = 0.8          # quadro final congelado pra chamada respirar
LEG_Y = 1450             # legenda abaixo da boca
BRANCO, PRETO = (255, 255, 255), (0, 0, 0)

def ease(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def com_alpha(img, k):
    if k >= 0.999: return img
    a = img.getchannel('A').point(lambda v: int(v * max(k, 0)))
    img = img.copy(); img.putalpha(a); return img
def escala(img, s):
    if abs(s - 1) < 1e-3: return img
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
def centro(img, cx, cy): return (img, int(cx - img.width / 2), int(cy - img.height / 2))
def recortar(img):
    bb = img.getbbox(); return (img.crop(bb), bb[0], bb[1]) if bb else None
def cartao(w, h, cor=(18, 18, 18, 220), r=28, sombra=True):
    pad = 30 if sombra else 0
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad))
    if sombra:
        sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + w, pad + h + 8), r, fill=(0, 0, 0, 120))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=cor)
    return im, pad
def texto_img(linhas, borda=8):
    """linhas: [(texto, fonte, cor)] centralizadas."""
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    medidas = [tmp.textbbox((0, 0), t, font=f, stroke_width=borda) for t, f, _ in linhas]
    w = int(max(b[2] - b[0] for b in medidas)) + 10
    hs = [int(f.size * 1.15) for _, f, _ in linhas]
    im = Image.new('RGBA', (w, sum(hs) + 20)); d = ImageDraw.Draw(im); y = 10
    for (t, f, c), h in zip(linhas, hs):
        d.text((w / 2, y + h / 2), t, font=f, fill=c, anchor='mm', stroke_width=borda, stroke_fill=PRETO); y += h
    return im
def saida(t, a): return 1 - ease((t - (a['fim'] - 0.2)) / 0.2) if t > a['fim'] - 0.2 else 1

# ---------- animações ----------
def an_impacto(a, t):
    lt = t - a['ini']
    if not hasattr(an_impacto, 'c'): an_impacto.c = {}
    key = a['texto']
    if key not in an_impacto.c:
        linhas = a['texto'].split('\n'); sz = a.get('tam', 180)
        an_impacto.c[key] = texto_img([(l, anton(sz if i == 0 else int(sz * 0.8)), ACC if i == len(linhas) - 1 else BRANCO) for i, l in enumerate(linhas)], borda=10)
    img = an_impacto.c[key]
    if lt < 0.2: s = 0.6 + 0.48 * ease(lt / 0.2)
    elif lt < 0.3: s = 1.08 - 0.08 * ((lt - 0.2) / 0.1)
    else: s = 1.0
    k = min(1, lt / 0.08) * saida(t, a)
    dx = dy = 0
    f = int((lt - 0.3) * FPS)
    if 0 <= f < 3: dx, dy = [(3, -2), (-2, 3), (2, 1)][f]
    im, x, y = centro(escala(img, s), 540 + dx, a.get('cy', 470) + dy)
    return [(com_alpha(im, k), x, y)]

def an_lista(a, t):
    lt = t - a['ini']; itens = a['itens']
    w, pad_x, linha = 800, 34, 92
    tit_h = 76 if a.get('titulo') else 0
    h = 30 + tit_h + linha * len(itens) + 20
    base, p = cartao(w, h)
    k_card = min(1, lt / 0.2) * saida(t, a)
    d = ImageDraw.Draw(base)
    if a.get('titulo'):
        d.text((p + pad_x, p + 30 + tit_h / 2 - 6), a['titulo'], font=mont(42, 900), fill=ACC, anchor='lm')
    fonte = mont(46, 800)
    for i, (txt, ti) in enumerate(itens):
        it = t - ti + 0.1
        if it < 0: continue
        cy = p + 30 + tit_h + linha * i + linha / 2
        k = ease(it / 0.2); dx = -40 * (1 - k)
        cx_ck = p + pad_x + 26 + dx
        camada = Image.new('RGBA', base.size); dc = ImageDraw.Draw(camada)
        arco = ease((it - 0.1) / 0.2)
        if arco > 0:
            dc.arc((cx_ck - 24, cy - 24, cx_ck + 24, cy + 24), -90, -90 + 360 * arco, fill=ACC, width=6)
        if it > 0.3:
            dc.ellipse((cx_ck - 24, cy - 24, cx_ck + 24, cy + 24), fill=ACC)
            dc.line([(cx_ck - 11, cy + 1), (cx_ck - 3, cy + 10), (cx_ck + 12, cy - 9)], fill=PRETO, width=7, joint='curve')
        f = fonte; mx = w - pad_x * 2 - 80
        while dc.textlength(txt, font=f) > mx: f = mont(f.size - 2, 800)
        dc.text((cx_ck + 46, cy), txt, font=f, fill=BRANCO, anchor='lm')
        base = Image.alpha_composite(base, com_alpha(camada, k))
    return [(com_alpha(base, k_card), 140 - p, a.get('y', 250) - p)]

def an_numero(a, t):
    lt = t - a['ini']
    passos = a['passos']  # [(tempo_abs, de, ate, rotulo)]
    atual = None
    for pz in passos:
        if t >= pz[0] - 0.1: atual = pz
    t0, de, ate, rot = atual
    p = ease((t - (t0 - 0.1)) / 0.8)
    val = int(round(de + (ate - de) * p))
    pulo = 1 + 0.15 * (1 - ease((t - (t0 - 0.1)) / 0.25)) if atual is not passos[0] else 1
    img = texto_img([(str(val), anton(230), ACC), (rot, mont(54, 900), BRANCO)], borda=9)
    s = (0.8 + 0.2 * ease(lt / 0.25)) * pulo
    k = min(1, lt / 0.2) * saida(t, a)
    im, x, y = centro(escala(img, s), 540, a.get('cy', 470))
    return [(com_alpha(im, k), x, y)]

def an_carimbo(a, t):
    lt = t - a['ini']
    if not hasattr(an_carimbo, 'img'):
        txt = texto_img([(a['sup'], mont(40, 900), ACC), (a['texto'], anton(124), ACC), (a['inf'], anton(76), BRANCO)], borda=0)
        w, h = txt.width + 70, txt.height + 40
        im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=(10, 10, 10, 190), outline=ACC, width=12)
        im.alpha_composite(txt, ((w - txt.width) // 2, (h - txt.height) // 2))
        an_carimbo.img = im.rotate(8, resample=Image.BICUBIC, expand=True)
    if lt < 0.12: s = 1.6 - 0.6 * ease(lt / 0.12)
    elif lt < 0.15: s = 1.0 + 0.05 * ((lt - 0.12) / 0.03)
    elif lt < 0.18: s = 1.05 - 0.05 * ((lt - 0.15) / 0.03)
    else: s = 1.0
    k = min(1, lt / 0.06) * saida(t, a)
    im, x, y = centro(escala(an_carimbo.img, s), 540, a.get('cy', 480))
    return [(com_alpha(im, k), x, y)]

def an_pilula(a, t):
    lt = t - a['ini']
    if not hasattr(an_pilula, 'img'):
        f = mont(54, 900); tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        tw = max(tmp.textlength(l, font=f) for l in a['linhas'])
        w, h = int(tw + 90), 70 * len(a['linhas']) + 50
        im, p = cartao(w, h, cor=ACC + (255,), r=36)
        d = ImageDraw.Draw(im)
        for i, l in enumerate(a['linhas']):
            d.text((p + w / 2, p + 25 + 70 * i + 35), l, font=f, fill=PRETO, anchor='mm')
        an_pilula.img = im
    k = ease(lt / 0.3)
    y = a.get('cy', 420) - 200 * (1 - k)
    if t > a['fim'] - 0.2: y -= 120 * ease((t - (a['fim'] - 0.2)) / 0.2)
    im, x, yy = centro(an_pilula.img, 540, y)
    return [(com_alpha(im, min(1, lt / 0.2) * saida(t, a)), x, yy)]

def an_comentario(a, t):
    lt = t - a['ini']; msg = a['texto']
    w, h = 800, 140
    im, p = cartao(w, h, cor=(255, 255, 255, 245), r=70)
    d = ImageDraw.Draw(im)
    cy = p + h / 2
    d.ellipse((p + 22, cy - 40, p + 102, cy + 40), fill=(220, 220, 225))
    d.ellipse((p + 46, cy - 26, p + 78, cy + 6), fill=(160, 160, 170)); d.pieslice((p + 34, cy + 4, p + 90, cy + 56), 180, 360, fill=(160, 160, 170))
    n = min(len(msg), max(0, int(lt / 0.05)))
    f = mont(46, 700)
    d.text((p + 126, cy), msg[:n], font=f, fill=(25, 25, 25), anchor='lm')
    if n < len(msg) or int(lt * 3) % 2 == 0:
        xc = p + 128 + d.textlength(msg[:n], font=f)
        d.line([(xc, cy - 26), (xc, cy + 26)], fill=(25, 25, 25), width=4)
    fim_dig = len(msg) * 0.05
    pulso = 1.0
    if lt > fim_dig + 0.15:
        q = (lt - fim_dig - 0.15)
        pulso = 1 + 0.18 * math.exp(-q * 6) * abs(math.sin(q * 10))
    r = 42 * pulso; bx = p + w - 70
    d.ellipse((bx - r, cy - r, bx + r, cy + r), fill=ACC)
    d.polygon([(bx - 16, cy - 20), (bx + 22, cy), (bx - 16, cy + 20), (bx - 8, cy)], fill=PRETO)
    k = ease(lt / 0.3)
    y = a.get('y', 330) + 60 * (1 - k)
    return [(com_alpha(im, min(1, lt / 0.2) * saida(t, a)), 140 - p, int(y - p))]

FUNCS = {'impacto': an_impacto, 'lista': an_lista, 'numero': an_numero, 'carimbo': an_carimbo,
         'pilula': an_pilula, 'comentario': an_comentario}

# ---------- legenda ----------
def grupos(palavras):
    gs, g = [], []
    for i, w in enumerate(palavras):
        if g:
            ant = g[-1]
            quebra = len(g) >= 3 or ant['w'][-1] in ',.?!' or w['s'] - ant['e'] > 0.3 \
                or sum(len(x['w']) for x in g) + len(w['w']) > 16
            if quebra: gs.append(g); g = []
        g.append(w)
    if g: gs.append(g)
    out = []
    for i, g in enumerate(gs):
        ini = g[0]['s']; fim = g[-1]['e']
        prox = gs[i + 1][0]['s'] if i + 1 < len(gs) else fim + 0.4
        fim = prox if prox - fim < 0.4 else fim + 0.25
        out.append({'ini': ini, 'fim': fim, 'ws': g})
    return out

def limpa(w): return w.strip(',.!').replace('etc', 'ETC.') if w.strip(',.!') else w

# ---------- sons ----------
SR = 48000
def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t * d)
def som(tipo):
    rng = np.random.default_rng(7)
    if tipo == 'whoosh':
        n = int(0.5 * SR); t = np.arange(n) / SR
        x = rng.standard_normal(n); x = np.convolve(x, np.ones(12) / 12, 'same')
        x = x - np.convolve(x, np.ones(80) / 80, 'same')
        e = np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2; return x * e
    if tipo == 'swish':
        n = int(0.25 * SR); t = np.arange(n) / SR
        x = rng.standard_normal(n); x = x - np.convolve(x, np.ones(30) / 30, 'same')
        return x * np.sin(np.pi * t / 0.25) ** 2
    if tipo == 'pop':
        n = int(0.09 * SR); t = np.arange(n) / SR
        f = 500 + 700 * np.exp(-t * 45); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 38)
    if tipo == 'impacto':
        n = int(0.6 * SR); t = np.arange(n) / SR
        f = 50 + 90 * np.exp(-t * 18)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 7)
        x += 0.35 * rng.standard_normal(n) * env(n, 0.001, 60); return x
    if tipo == 'seco':
        n = int(0.3 * SR); t = np.arange(n) / SR
        f = 90 + 120 * np.exp(-t * 30)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 16) + 0.5 * rng.standard_normal(n) * env(n, 0.0005, 90)
    if tipo == 'ding':
        n = int(0.9 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t) + 0.2 * np.sin(2 * np.pi * 3951 * t)) * env(n, 0.002, 5)
    if tipo == 'clique':
        n = int(0.04 * SR); return rng.standard_normal(n) * env(n, 0.0003, 250) + np.sin(2 * np.pi * 2500 * np.arange(n) / SR) * env(n, 0.0003, 180)
    if tipo == 'teclado':
        n = int(1.0 * SR); x = np.zeros(n)
        for i in range(18):
            p = int(i * 0.05 * SR + rng.integers(0, 300)); m = int(0.02 * SR)
            x[p:p + m] += rng.standard_normal(m) * env(m, 0.0002, 400) * rng.uniform(0.6, 1)
        return x
    raise ValueError(tipo)

def mixar(pasta, sfx, dur_total):
    def run(*a): return subprocess.run(a, capture_output=True, text=True)
    # voz normalizada (-14 LUFS, 2 passadas)
    def loudnorm(src, dst, extra_in=()):
        r = run('ffmpeg', '-hide_banner', *extra_in, '-i', src, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-')
        js = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
        f = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
             f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
        r2 = run('ffmpeg', '-v', 'error', '-y', *extra_in, '-i', src, '-af', f + f',aresample={SR}', '-ac', '2', '-c:a', 'pcm_s16le', dst)
        assert r2.returncode == 0, r2.stderr
    loudnorm(f'{pasta}/base.mov', f'{pasta}/voz.wav')
    wf = wave.open(f'{pasta}/voz.wav'); voz = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768
    n = int(dur_total * SR); mix = np.zeros((n, 2), np.float32); mix[:min(n, len(voz))] = voz[:n]
    ultimo = -9
    for t, tipo, db in sorted(sfx):
        assert t - ultimo >= 0.6 - 1e-6, f'sons muito juntos em {t}'; ultimo = t
        x = som(tipo); x = x / (np.abs(x).max() + 1e-9) * 10 ** (db / 20)
        p = int(max(t, 0) * SR); m = min(len(x), n - p)
        if m > 0: mix[p:p + m] += x[:m, None]
    pre = f'{pasta}/mix_pre.wav'
    with wave.open(pre, 'wb') as o:
        o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
        o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    loudnorm(pre, f'{pasta}/mix.wav')

# ---------- montagem ----------
def main():
    pasta, t0 = sys.argv[1], float(sys.argv[2])
    plano = json.load(open(f'{pasta}/plano.json'))
    dur_base = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{pasta}/base.mov'], capture_output=True, text=True).stdout)
    dur_total = dur_base + EXTRA_FIM
    t1 = dur_total if sys.argv[3] == 'fim' else float(sys.argv[3])
    saida_mp4 = sys.argv[4]

    # áudio do vídeo todo (uma vez)
    import os
    if not os.path.exists(f'{pasta}/mix.wav') or os.path.getmtime(f'{pasta}/mix.wav') < os.path.getmtime(f'{pasta}/plano.json'):
        mixar(pasta, [tuple(s) for s in plano['sons']], dur_total)

    leg = grupos(json.load(open(f'{pasta}/palavras.json')))
    cache_leg = {}
    def camada_legenda(t):
        for g in leg:
            if g['ini'] - 0.05 <= t < g['fim']:
                at = 0
                for j, w in enumerate(g['ws']):
                    if t >= w['s'] - 0.05: at = j
                key = (id(g), at)
                if key not in cache_leg:
                    ws = [limpa(w['w']) for w in g['ws']]
                    cache_leg[key] = recortar(legenda_impacto(ws, at, LEG_Y))
                return cache_leg[key]
        return None
    gk = plano['gancho']
    gancho_imgs = {}
    def camada_gancho(t):
        if not (0 <= t < gk['fim']): return None
        q = min(3, int(t * FPS)); s = [0.9, 0.933, 0.966, 1.0][q]
        if s not in gancho_imgs: gancho_imgs[s] = recortar(gancho_manchete(gk['l1'], gk['l2'], escala=s, top=300 + int(130 * (1 - s))))
        im, x, y = gancho_imgs[s]
        k = min(1, (t + 1 / FPS) / (4 / FPS))
        if t > gk['fim'] - 0.15: k = (gk['fim'] - t) / 0.15
        return (com_alpha(im, k), x, y)

    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-i', f'{pasta}/base.mov', '-t', f'{t1 - t0:.3f}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', f'{pasta}/mix.wav',
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', saida_mp4], stdin=subprocess.PIPE)
    nf = int(round((t1 - t0) * FPS)); tam = W * H * 3; ultimo = None
    for i in range(nf):
        b = dec.stdout.read(tam)
        if len(b) == tam: ultimo = b
        t = t0 + i / FPS
        fr = Image.frombytes('RGB', (W, H), ultimo)
        cams = []
        g = camada_gancho(t)
        if g: cams.append(g)
        ativas = [a for a in plano['animacoes'] if a['ini'] - 0.0 <= t < a['fim']]
        esconde_leg = any(a.get('esconde_legenda') for a in ativas)
        for a in ativas: cams += FUNCS[a['tipo']](a, t)
        if not esconde_leg:
            c = camada_legenda(t)
            if c: cams.append(c)
        for im, x, y in cams: fr.paste(im, (x, y), im)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    print('ok', saida_mp4, nf, 'quadros')

if __name__ == '__main__':
    main()
