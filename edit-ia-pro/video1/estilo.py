from PIL import Image, ImageDraw, ImageFont
F = '/home/user/Edi-o-de-v-deos-/edit-ia-pro/ferramentas/'
W, H = 1080, 1920
ACC = (255, 196, 0)
def anton(sz): return ImageFont.truetype(F + 'Anton-Regular.ttf', sz)
def mont(sz, wt=800):
    f = ImageFont.truetype(F + 'Montserrat.ttf', sz); f.set_variation_by_axes([wt]); return f

def legenda_impacto(palavras, ativa, cy, size=90, acc=ACC, maxw=800):
    """Impacto: Anton caixa alta, contorno preto 8px, palavra falada na cor de destaque."""
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    f = anton(size); sp = int(size * 0.28)
    ws = [p.upper() for p in palavras]
    wid = [d.textlength(w, font=f) for w in ws]
    tot = sum(wid) + sp * (len(ws) - 1)
    while tot > maxw and size > 60:
        size -= 4; f = anton(size); sp = int(size * 0.28)
        wid = [d.textlength(w, font=f) for w in ws]; tot = sum(wid) + sp * (len(ws) - 1)
    x = (W - tot) / 2
    for i, w in enumerate(ws):
        d.text((x, cy), w, font=f, anchor='lm', fill=acc if i == ativa else (255, 255, 255),
               stroke_width=8, stroke_fill=(0, 0, 0))
        x += wid[i] + sp
    return im

def gancho_manchete(l1, l2, top=300, size=110, acc=ACC, escala=1.0):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    while max(d.textlength(t.upper(), font=anton(size)) for t in (l1, l2)) > 780: size -= 2
    f = anton(int(size * escala)); lh = int(size * 1.22 * escala)
    cy = top + lh // 2
    for txt, cor in ((l1, (255, 255, 255)), (l2, acc)):
        d.text((W / 2, cy), txt.upper(), font=f, anchor='mm', fill=cor, stroke_width=int(9 * escala), stroke_fill=(0, 0, 0))
        cy += lh
    return im
