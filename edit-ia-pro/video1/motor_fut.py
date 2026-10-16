"""Versão Futurista: neon + vidro + HUD + glitch + ícones 3D.
Uso: python3 motor_fut.py <pasta_fut> <t0> <t1|fim> <saida.mp4>
A pasta_fut tem: base.mov (link), palavras.json, plano_fut.json
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motor
from motor import ease, com_alpha, escala, centro, recortar, grupos, limpa, env, SR
from futurista import (gradacao, texto_neon, painel_vidro, hud, legenda_neon, glitch,
                       orbitron, grotesk, mono, CIANO, MAGENTA, BRANCO, W, H)

FPS = 30
EXTRA_FIM = 0.8
LEG_Y = 1450
ICONES = '/home/user/Edi-o-de-v-deos-/edit-ia-pro/ferramentas/icones3d/'

def saida(t, a, d=0.2): return 1 - ease((t - (a['fim'] - d)) / d) if t > a['fim'] - d else 1

def fantasma_rgb(img, dx):
    """Separação de cor só na camada (entrada com falha digital)."""
    if dx == 0: return img
    al = img.getchannel('A')
    out = Image.new('RGBA', (img.width + 2 * abs(dx), img.height))
    for cor, off in ((MAGENTA, 0), (CIANO, 2 * abs(dx))):
        c = Image.new('RGBA', img.size, cor + (0,)); c.putalpha(al.point(lambda v: int(v * 0.7)))
        out.alpha_composite(c, (off, 0))
    out.alpha_composite(img, (abs(dx), 0))
    return out

def entrada_falha(lt):
    f = int(lt * FPS)
    return [14, -9, 6, -3][f] if 0 <= f < 4 else 0

# ---------- ícones 3D ----------
_ic = {}
def icone_base(nome, tam):
    k = (nome, tam)
    if k not in _ic:
        im = Image.open(ICONES + nome + '_3d.png').convert('RGBA').resize((tam, tam), Image.LANCZOS)
        pad = 40
        out = Image.new('RGBA', (tam + 2 * pad, tam + 2 * pad))
        g = Image.new('RGBA', out.size, CIANO + (0,))
        m = Image.new('L', out.size); m.paste(im.getchannel('A'), (pad, pad))
        g.putalpha(m.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.6)))
        out.alpha_composite(g)
        sombra = Image.new('RGBA', out.size, (0, 0, 0, 0)); ms = Image.new('L', out.size); ms.paste(im.getchannel('A'), (pad + 6, pad + 14))
        sombra.putalpha(ms.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.45)))
        out.alpha_composite(sombra)
        out.alpha_composite(im, (pad, pad))
        _ic[k] = out
    return _ic[k]

def camada_icone(a, t):
    lt = t - a['ini']; tam = a.get('tam', 170)
    base = icone_base(a['icone'], tam)
    # entrada: pulo com mola + giro (meia volta no eixo vertical)
    if lt < 0.45:
        p = lt / 0.45
        s = 1 + 0.25 * math.exp(-6 * p) * math.sin(p * 10) if p > 0.15 else ease(p / 0.15) * 1.1
        giro = abs(math.cos((1 - ease(p)) * math.pi))
    else:
        s, giro = 1.0, 1.0
    # flutuar + balançar
    fy = 10 * math.sin((t + a['ini']) * 2.6)
    ang = 6 * math.sin((t + a['ini'] * 1.7) * 1.9)
    # saída: encolhe
    if t > a['fim'] - 0.22:
        s *= 1 - ease((t - (a['fim'] - 0.22)) / 0.22)
    if s <= 0.02: return []
    im = base.resize((max(2, int(base.width * s * max(giro, 0.06))), max(2, int(base.height * s))), Image.BICUBIC)
    if abs(ang) > 0.3: im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    x, y = a['pos']
    return [centro(im, x, y + fy)]

# ---------- animações (versão futurista) ----------
_cache = {}
def f_impacto(a, t, fr):
    lt = t - a['ini']; key = ('imp', a['texto'])
    if key not in _cache:
        linhas = a['texto'].split('\n'); sz = a.get('tam', 150)
        ims = [texto_neon(l, orbitron(sz if i == 0 else int(sz * 0.72)), cor=BRANCO,
                          brilho=MAGENTA if i == len(linhas) - 1 and len(linhas) > 1 else CIANO, raio=20, forca=1.3, contorno=2)
               for i, l in enumerate(linhas)]
        w = max(i.width for i in ims); h = sum(i.height for i in ims) - 60 * (len(ims) - 1)
        out = Image.new('RGBA', (w, h)); y = 0
        for i in ims: out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height - 60
        _cache[key] = out
    img = _cache[key]
    if lt < 0.2: s = 0.6 + 0.48 * ease(lt / 0.2)
    elif lt < 0.3: s = 1.08 - 0.08 * ((lt - 0.2) / 0.1)
    else: s = 1.0
    img = fantasma_rgb(escala(img, s), entrada_falha(lt))
    k = min(1, lt / 0.06) * saida(t, a)
    im, x, y = centro(img, 540, a.get('cy', 450))
    return [(com_alpha(im, k), x, y)]

def f_lista(a, t, fr):
    lt = t - a['ini']; itens = a['itens']
    linha, tit_h = 100, 70
    vis = sum(ease((t - ti + 0.1) / 0.2) for _, ti in itens if t >= ti - 0.1)
    vis = max(vis, 1.0)
    y0 = a.get('y', 250); h = int(26 + tit_h + linha * vis + 16)
    k_card = min(1, lt / 0.2) * saida(t, a)
    painel, px, py = painel_vidro(fr, (140, y0, 940, y0 + h))
    d = ImageDraw.Draw(painel); ox, oy = 140 - px, y0 - py
    d.text((ox + 36, oy + 26 + tit_h / 2 - 4), '// ' + a['titulo'], font=mono(34), fill=CIANO, anchor='lm')
    for i, (txt, ti) in enumerate(itens):
        it = t - ti + 0.1
        if it < 0: continue
        cy = oy + 26 + tit_h + linha * i + linha / 2
        k = ease(it / 0.2); dx = -40 * (1 - k)
        cam = Image.new('RGBA', painel.size); dc = ImageDraw.Draw(cam)
        bx = ox + 58 + dx
        q = ease((it - 0.08) / 0.15)
        if q > 0: dc.rounded_rectangle((bx - 22, cy - 22, bx + 22, cy + 22), 8, outline=CIANO, width=4)
        if it > 0.25:
            dc.line([(bx - 11, cy + 1), (bx - 2, cy + 11), (bx + 14, cy - 11)], fill=CIANO, width=6, joint='curve')
        f = grotesk(52, 700)
        while dc.textlength(txt, font=f) > 800 - 150: f = grotesk(f.size - 2, 700)
        dc.text((bx + 46, cy), txt, font=f, fill=BRANCO, anchor='lm')
        painel = Image.alpha_composite(painel, com_alpha(cam, k))
    return [(com_alpha(painel, k_card), px, py)]

def f_numero(a, t, fr):
    lt = t - a['ini']; atual = a['passos'][0]
    for pz in a['passos']:
        if t >= pz[0] - 0.1: atual = pz
    t0, de, ate, rot = atual
    p = ease((t - (t0 - 0.1)) / 0.8)
    val = int(round(de + (ate - de) * p))
    key = ('num', val, rot)
    if key not in _cache:
        n = texto_neon(str(val), orbitron(240), cor=BRANCO, brilho=MAGENTA, raio=26, forca=1.5)
        l = texto_neon(rot, mono(50), cor=CIANO, brilho=CIANO, raio=8, forca=0.6)
        out = Image.new("RGBA", (max(n.width, l.width), n.height + l.height - 50))
        out.alpha_composite(n, ((out.width - n.width) // 2, 0)); out.alpha_composite(l, ((out.width - l.width) // 2, n.height - 50))
        _cache[key] = out
    img = escala(_cache[key], 0.8 + 0.2 * ease(lt / 0.25))
    img = fantasma_rgb(img, entrada_falha(t - (t0 - 0.1)))
    im, x, y = centro(img, 540, a.get('cy', 450))
    return [(com_alpha(im, min(1, lt / 0.2) * saida(t, a)), x, y)]

def f_carimbo(a, t, fr):
    lt = t - a['ini']
    w, h = 720, 330; x0, y0 = 180, a.get('y', 300)
    painel, px, py = painel_vidro(fr, (x0, y0, x0 + w, y0 + h), borda=MAGENTA)
    ox, oy = x0 - px, y0 - py
    if 'carimbo_txt' not in _cache:
        _cache['carimbo_txt'] = [texto_neon(a['sup'], mono(34), cor=CIANO, brilho=CIANO, raio=6, forca=0.5),
                                 texto_neon(a['texto'], orbitron(92), cor=BRANCO, brilho=MAGENTA, raio=18, forca=1.3),
                                 texto_neon(a['inf'], orbitron(50), cor=BRANCO, brilho=CIANO, raio=10, forca=0.8)]
    ys = [oy + 62, oy + 160, oy + 262]
    for im, cy in zip(_cache['carimbo_txt'], ys):
        painel.alpha_composite(im, (ox + w // 2 - im.width // 2, int(cy - im.height / 2)))
    if lt < 0.12: s = 1.5 - 0.5 * ease(lt / 0.12)
    elif lt < 0.15: s = 1.0 + 0.05 * ((lt - 0.12) / 0.03)
    elif lt < 0.18: s = 1.05 - 0.05 * ((lt - 0.15) / 0.03)
    else: s = 1.0
    img = fantasma_rgb(escala(painel, s), entrada_falha(lt))
    im, x, y = centro(img, x0 + w / 2, y0 + h / 2)
    return [(com_alpha(im, min(1, lt / 0.06) * saida(t, a)), x, y)]

def f_pilula(a, t, fr):
    lt = t - a['ini']
    k = ease(lt / 0.3); dy = -160 * (1 - k)
    if t > a['fim'] - 0.2: dy -= 100 * ease((t - (a['fim'] - 0.2)) / 0.2)
    w, h = 760, 190; x0 = 160; y0 = int(a.get('y', 300) + dy)
    painel, px, py = painel_vidro(fr, (x0, max(0, y0), x0 + w, max(0, y0) + h), raio=60)
    ox, oy = x0 - px, max(0, y0) - py
    for i, l in enumerate(a['linhas']):
        g = texto_neon(l, orbitron(52), cor=BRANCO, brilho=CIANO, raio=10, forca=0.8)
        painel.alpha_composite(g, (ox + w // 2 - g.width // 2, int(oy + 60 + 72 * i - g.height / 2)))
    return [(com_alpha(painel, min(1, lt / 0.2) * saida(t, a)), px, py)]

def f_comentario(a, t, fr):
    lt = t - a['ini']; msg = a['texto']
    w, h = 800, 140; x0, y0 = 140, int(a.get('y', 330) + 50 * (1 - ease(lt / 0.3)))
    painel, px, py = painel_vidro(fr, (x0, y0, x0 + w, y0 + h), raio=70)
    d = ImageDraw.Draw(painel); ox, oy = x0 - px, y0 - py; cy = oy + h / 2
    n = min(len(msg), max(0, int(lt / 0.05)))
    f = mono(44)
    d.text((ox + 44, cy), msg[:n], font=f, fill=BRANCO, anchor='lm')
    if n < len(msg) or int(lt * 3) % 2 == 0:
        xc = ox + 48 + d.textlength(msg[:n], font=f)
        d.rectangle((xc, cy - 24, xc + 18, cy + 24), fill=CIANO)
    fim_dig = len(msg) * 0.05; pulso = 1.0
    if lt > fim_dig + 0.15:
        q = lt - fim_dig - 0.15; pulso = 1 + 0.2 * math.exp(-q * 6) * abs(math.sin(q * 10))
    r = 44 * pulso; bx = ox + w - 72
    d.ellipse((bx - r, cy - r, bx + r, cy + r), fill=CIANO)
    d.polygon([(bx - 16, cy - 20), (bx + 22, cy), (bx - 16, cy + 20), (bx - 8, cy)], fill=(5, 10, 25))
    return [(com_alpha(painel, min(1, lt / 0.2) * saida(t, a)), px, py)]

FUNCS = {'impacto': f_impacto, 'lista': f_lista, 'numero': f_numero, 'carimbo': f_carimbo,
         'pilula': f_pilula, 'comentario': f_comentario, 'icone': lambda a, t, fr: camada_icone(a, t)}

# ---------- sons eletrônicos ----------
som_antigo = motor.som
def som(tipo):
    rng = np.random.default_rng(11)
    if tipo == 'bip':
        n = int(0.12 * SR); t = np.arange(n) / SR
        f = 900 + 1400 * (1 - np.exp(-t * 60))
        return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.35 + np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, 0.002, 30)
    if tipo == 'glitch':
        n = int(0.28 * SR); x = np.zeros(n)
        for i in range(6):
            p = int(rng.uniform(0, 0.22) * SR); m = int(rng.uniform(0.01, 0.04) * SR)
            seg = np.sign(rng.standard_normal(m // 40 + 1)).repeat(40)[:m] * rng.uniform(0.4, 1)
            x[p:p + m] += seg[:len(x[p:p + m])]
        return x * env(n, 0.001, 6)
    if tipo == 'sweep':
        n = int(0.55 * SR); t = np.arange(n) / SR
        f = 200 * (12 ** (t / 0.55))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + rng.standard_normal(n) * 0.25
        return x * np.sin(np.pi * t / 0.55) ** 2
    if tipo == 'drop':
        n = int(0.7 * SR); t = np.arange(n) / SR
        f = 45 + 160 * np.exp(-t * 14)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 5)
        gl = som('glitch'); x[:len(gl)] += 0.35 * gl
        return x
    return som_antigo(tipo)
motor.som = som

# ---------- montagem ----------
def main():
    pasta, t0 = sys.argv[1], float(sys.argv[2])
    plano = json.load(open(f'{pasta}/plano_fut.json'))
    dur_base = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{pasta}/base.mov'], capture_output=True, text=True).stdout)
    dur_total = dur_base + EXTRA_FIM
    t1 = dur_total if sys.argv[3] == 'fim' else float(sys.argv[3])
    out_mp4 = sys.argv[4]
    if not os.path.exists(f'{pasta}/mix.wav') or os.path.getmtime(f'{pasta}/mix.wav') < os.path.getmtime(f'{pasta}/plano_fut.json'):
        motor.mixar(pasta, [tuple(s) for s in plano['sons']], dur_total)

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
                    cache_leg[key] = recortar(legenda_neon([limpa(w['w']) for w in g['ws']], at, LEG_Y))
                return cache_leg[key]
        return None

    gk = plano['gancho']
    g1 = texto_neon(gk['l1'].upper(), orbitron(50), cor=BRANCO, brilho=CIANO, raio=8, forca=0.5)
    g2 = texto_neon(gk['l2'].upper(), orbitron(88), cor=BRANCO, brilho=CIANO, raio=20, forca=1.2, contorno=2)
    def camadas_gancho(t, fr):
        if not (0 <= t < gk['fim']): return []
        painel, px, py = painel_vidro(fr, (140, 300, 940, 580))
        painel.alpha_composite(g1, (540 - px - g1.width // 2, 380 - py - g1.height // 2))
        painel.alpha_composite(g2, (540 - px - g2.width // 2, 490 - py - g2.height // 2))
        s = [0.9, 0.94, 0.97, 1.0][min(3, int(t * FPS))]
        img = fantasma_rgb(escala(painel, s), entrada_falha(t))
        k = min(1, (t + 1 / FPS) / (4 / FPS))
        if t > gk['fim'] - 0.2: k = (gk['fim'] - t) / 0.2
        im, x, y = centro(img, 540, 440)
        return [(com_alpha(im, k), x, y)]

    hud_cfg = plano['hud']
    falhas = plano['glitches']  # tempos de falha digital (3 quadros)

    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-i', f'{pasta}/base.mov', '-t', f'{t1 - t0:.3f}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', f'{pasta}/mix.wav',
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_mp4], stdin=subprocess.PIPE)
    nf = int(round((t1 - t0) * FPS)); tam = W * H * 3; ultimo = None
    for i in range(nf):
        b = dec.stdout.read(tam)
        if len(b) == tam: ultimo = b
        t = t0 + i / FPS
        arr = gradacao(np.frombuffer(ultimo, np.uint8).reshape(H, W, 3))
        for gt in falhas:
            q = int((t - gt) * FPS)
            if 0 <= q < 3: arr = glitch(arr, [1.0, 0.6, 0.3][q], semente=int(gt * 100) + q)
        fr = Image.fromarray(arr)
        cams = []
        for hc in hud_cfg:
            if hc['ini'] <= t < hc['fim']:
                k = min(1, (t - hc['ini']) / 0.3) * saida(t, hc, 0.3)
                cams.append((hud(t, tuple(hc['rosto']), k=k, rotulo=hc.get('rotulo', '')), 0, 0))
        cams += camadas_gancho(t, fr)
        ativas = [a for a in plano['animacoes'] if a['ini'] <= t < a['fim']]
        for a in ativas: cams += FUNCS[a['tipo']](a, t, fr)
        c = camada_legenda(t)
        if c: cams.append(c)
        for im, x, y in cams: fr.paste(im, (int(x), int(y)), im)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    print('ok', out_mp4, nf, 'quadros')

if __name__ == '__main__':
    main()
