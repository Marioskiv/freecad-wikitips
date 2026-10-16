import json, os, sys, io
from PIL import Image, ImageSequence
import cairosvg
SRC, JS, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
MW, MH = 420, 300
os.makedirs(OUTDIR, exist_ok=True)
data = json.load(open(JS, encoding='utf-8'))
done, missing = {}, 0
def fit(im):
    im.thumbnail((MW, MH), Image.LANCZOS); return im
for k, e in data.items():
    f = e.get('i')
    if not f: continue
    if f in done:
        e['i'] = done[f]; continue
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        e.pop('i'); missing += 1; continue
    stem = os.path.splitext(f)[0]
    try:
        ext = f.lower().rsplit('.', 1)[-1]
        if ext == 'svg':
            png = cairosvg.svg2png(url=p, output_width=MW*2)
            im = Image.open(io.BytesIO(png)).convert('RGBA')
            bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
            im = fit(bg.convert('RGB')); out = stem + '.png'; im.save(os.path.join(OUTDIR, out), optimize=True)
        elif ext == 'gif':
            src = Image.open(p)
            frames = [fit(fr.convert('RGB')) for fr in ImageSequence.Iterator(src)]
            out = stem + '.gif'
            frames[0].save(os.path.join(OUTDIR, out), save_all=True, append_images=frames[1:], loop=0,
                           duration=src.info.get('duration', 100), optimize=True)
        else:
            im = Image.open(p)
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
            im = fit(im.convert('RGB'))
            # few colours (screenshots/diagrams) -> png, photos -> jpg
            if len(im.getcolors(4096) or []) and im.getcolors(4096) is not None:
                out = stem + '.png'; im.quantize(256).save(os.path.join(OUTDIR, out), optimize=True)
            else:
                out = stem + '.jpg'; im.save(os.path.join(OUTDIR, out), quality=82, optimize=True)
        done[f] = out; e['i'] = out
    except Exception as ex:
        print('fail', f, ex); e.pop('i', None); missing += 1
json.dump(data, open(JS, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(done), 'images,', missing, 'missing')
