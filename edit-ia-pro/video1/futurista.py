"""Estilo Futurista (neon + HUD + vidro + glitch)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
F = '/home/user/Edi-o-de-v-deos-/edit-ia-pro/ferramentas/'
W, H = 1080, 1920
CIANO = (0, 229, 255)
MAGENTA = (255, 43, 214)
BRANCO = (255, 255, 255)

def orbitron(sz, wt=900):
    f = ImageFont.truetype(F + 'Orbitron.ttf', sz); f.set_variation_by_axes([wt]); return f
def grotesk(sz, wt=700):
    f = ImageFont.truetype(F + 'SpaceGrotesk.ttf', sz); f.set_variation_by_axes([wt]); return f
def mono(sz): return ImageFont.truetype(F + 'SpaceMono-Bold.ttf', sz)

# ---------- cor ----------
_VIN = None
def gradacao(fr):
    """Cor de cinema futurista: sombras azuladas, contraste, vinheta. fr: np uint8 HxWx3."""
    global _VIN
    if _VIN is None:
        y, x = np.ogrid[:H, :W]
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H * 0.48) / (H / 2)) ** 2)
        _VIN = (1 - 0.38 * np.clip(r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
    a = fr.astype(np.float32) / 255
    a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1)                      # contraste
    lum = a.mean(axis=2, keepdims=True)
    sombra = np.clip(1 - lum * 2, 0, 1)
    a = a + sombra * np.array([-0.035, 0.01, 0.05], np.float32)     # sombras azul-ciano
    a = a * _VIN
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)

# ---------- texto com brilho ----------
def texto_neon(txt, font, cor=BRANCO, brilho=CIANO, raio=14, forca=1.0, contorno=0):
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bb = tmp.textbbox((0, 0), txt, font=font, stroke_width=contorno)
    pad = raio * 3
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=font, fill=255, stroke_width=contorno + 2)
    glow = m.filter(ImageFilter.GaussianBlur(raio)).point(lambda v: min(255, int(v * 1.8 * forca)))
    im = Image.new('RGBA', (w, h), brilho + (0,)); im.putalpha(glow)
    d = ImageDraw.Draw(im)
    d.text((pad - bb[0], pad - bb[1]), txt, font=font, fill=cor, stroke_width=contorno, stroke_fill=(0, 0, 0))
    return im

# ---------- vidro ----------
def painel_vidro(fundo, caixa, raio=30, borda=CIANO, tinta=(8, 14, 28, 150)):
    """Recorta o fundo, desfoca e escurece (vidro fosco) com borda neon. Retorna (img, x, y)."""
    x0, y0, x1, y1 = caixa
    pad = 24
    reg = fundo.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(22)).convert('RGBA')
    reg = Image.alpha_composite(reg, Image.new('RGBA', reg.size, tinta))
    w, h = x1 - x0, y1 - y0
    out = Image.new('RGBA', (w + 2 * pad, h + 2 * pad))
    mask = Image.new('L', (w, h)); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), raio, fill=255)
    out.paste(reg, (pad, pad), mask)
    lin = Image.new('L', out.size); ImageDraw.Draw(lin).rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), raio, outline=255, width=3)
    glow = lin.filter(ImageFilter.GaussianBlur(9)).point(lambda v: min(255, v * 3))
    gi = Image.new('RGBA', out.size, borda + (0,)); gi.putalpha(glow)
    out = Image.alpha_composite(out, gi)
    ImageDraw.Draw(out).rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), raio, outline=borda + (255,), width=3)
    # brilho de vidro na parte de cima
    hl = Image.new('RGBA', out.size); ImageDraw.Draw(hl).rounded_rectangle((pad + 3, pad + 3, pad + w - 4, pad + h // 3), raio, fill=(255, 255, 255, 14))
    out = Image.alpha_composite(out, hl)
    return out, x0 - pad, y0 - pad

# ---------- HUD ----------
def hud(t, rosto, k=1.0, rotulo='ANÁLISE // ESCALA 6X1'):
    """Cantoneiras em volta do rosto + rótulos técnicos. rosto=(x,y,w,h)."""
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    x, y, w, h = rosto
    m = 40; x0, y0, x1, y1 = x - m, y - m, x + w + m, y + h + m
    L = 70; c = CIANO + (int(200 * k),)
    for (px, py, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py + sy * L), (px, py), (px + sx * L, py)], fill=c, width=5)
    # mira pequena nas laterais
    for yy in (y0 + (y1 - y0) // 2,):
        d.line([(x0 - 18, yy), (x0 + 10, yy)], fill=c, width=3); d.line([(x1 - 10, yy), (x1 + 18, yy)], fill=c, width=3)
    f = mono(26)
    d.text((x0, y1 + 14), rotulo, font=f, fill=CIANO + (int(230 * k),))
    pisca = int(t * 2) % 2 == 0
    d.ellipse((150, 252, 172, 274), fill=(255, 40, 60, int(255 * k)) if pisca else (255, 40, 60, int(90 * k)))
    d.text((184, 246), 'REC', font=mono(30), fill=BRANCO + (int(230 * k),))
    mm, ss, ff = int(t // 60), int(t % 60), int((t % 1) * 30)
    d.text((930, 246), f'{mm:02d}:{ss:02d}:{ff:02d}', font=mono(30), fill=BRANCO + (int(200 * k),), anchor='ra')
    gl = im.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(gl, im)

# ---------- legenda ----------
def legenda_neon(palavras, ativa, cy, size=86, maxw=800):
    f = orbitron(size); sp = int(size * 0.32)
    ws = [p.upper() for p in palavras]
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    while True:
        wid = [tmp.textlength(w, font=f) for w in ws]; tot = sum(wid) + sp * (len(ws) - 1)
        if tot <= maxw or size <= 56: break
        size -= 4; f = orbitron(size); sp = int(size * 0.32)
    im = Image.new('RGBA', (W, H)); x = (W - tot) / 2
    for i, w in enumerate(ws):
        if i == ativa:
            g = texto_neon(w, f, cor=BRANCO, brilho=CIANO, raio=16, forca=1.4, contorno=3)
        else:
            g = texto_neon(w, f, cor=(235, 240, 255), brilho=(0, 0, 0), raio=10, forca=0.9, contorno=3)
        pad = (g.width - wid[i]) / 2
        im.alpha_composite(g, (int(x - pad), int(cy - g.height / 2)))
        if i == ativa:
            ImageDraw.Draw(im).rounded_rectangle((x, cy + size * 0.62, x + wid[i], cy + size * 0.62 + 7), 3, fill=CIANO)
        x += wid[i] + sp
    return im

# ---------- glitch ----------
def glitch(fr, forca, semente=0):
    """fr: np HxWx3. Separação RGB + fatias deslocadas."""
    rng = np.random.default_rng(semente)
    o = fr.copy(); dx = int(18 * forca)
    o[..., 0] = np.roll(fr[..., 0], dx, axis=1); o[..., 2] = np.roll(fr[..., 2], -dx, axis=1)
    for _ in range(int(7 * forca) + 1):
        y = rng.integers(0, H - 80); h = rng.integers(8, 70); s = int(rng.integers(-60, 60) * forca)
        o[y:y + h] = np.roll(o[y:y + h], s, axis=1)
    return o
