import re, json, sys, os, html
WIKI = sys.argv[1]; OUT = sys.argv[2]

def strip_inline(s):
    s = re.sub(r'<img[^>]*>', '', s)
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', s)
    s = re.sub(r'<small>\s*\((v[\d.]+)\)\s*</small>', r'(\1)', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', '', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
    s = s.replace("\\'", "'").replace('\\"', '"')
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace('<b> ', '<b>').replace(' </b>', '</b>')
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s).replace('`', '')
    s = re.sub(r'(?<![<\w])\*+(?![\w>])', '', s)
    s = re.sub(r',?\s*\(?see (the )?(\w+ ){0,2}(below|above)\)?', '', s, flags=re.I)
    s = re.sub(r'\[\[|\]\]', '', s)
    s = re.sub(r'\s+([.,;:])', r'\1', s).strip()
    return s

def section(text, name):
    m = re.search(r'^## ' + name + r'\s*$(.*?)(?=^## |\Z)', text, re.M | re.S)
    return m.group(1) if m else ''

IMG_RE = re.compile(r'!\[[^\]]*\]\((images/[^)\s]+)\s*\)|<img[^>]*src="?(images/[^"\s>]+)"?[^>]*>', re.I)

def pick_image(block, name):
    for m in IMG_RE.finditer(block):
        src = (m.group(1) or m.group(2)).strip().replace('‎', '')
        tag = m.group(0)
        w = re.search(r'width[:=]\s*"?(\d+)', tag)
        if w and int(w.group(1)) < 100:
            continue
        base = os.path.basename(src)
        if base.lower() == (name + '.svg').lower():
            continue
        if re.search(r'(Taskpanel|TaskPanel|task_panel|_dialog|Dialog)', base) and 'Taskpanel' in base:
            pass
        return base
    return None

def paragraphs(block, limit=380):
    out, total = [], 0
    for para in re.split(r'\n\s*\n', block):
        p = para.strip()
        if not p or p.startswith('#') or p.startswith('<div') or p.startswith('|'):
            continue
        if re.fullmatch(r'(!\[.*?\]\(.*?\)|<img[^>]*>|\s)+', p, re.S):
            continue
        if p.startswith('*') and p.endswith('*') and not p.startswith('**'):
            continue  # image caption
        if re.match(r'^(\d+\.|-)\s', p):
            items = [strip_inline(x) for x in re.findall(r'^\s{0,3}(?:\d+\.|-)\s+(.*)$', p, re.M)]
            items = [i for i in items if i]
            if items:
                out.append('<ul>' + ''.join('<li>%s</li>' % i for i in items[:6]) + '</ul>')
                total += sum(len(i) for i in items[:6])
        else:
            t = strip_inline(p)
            if t and not re.fullmatch(r'<i>.*</i>', t):
                out.append('<p>%s</p>' % t); total += len(t)
        if total > limit:
            break
    return ''.join(out)

def usage_steps(block, maxn=6):
    steps = []
    for m in re.finditer(r'^(\d+)\.\s+(.*?)(?=^\d+\.\s|\Z)', block, re.M | re.S):
        body = m.group(2)
        first = body.split('\n')[0]
        t = strip_inline(first)
        if not t or re.search(r'several ways to invoke|ways to invoke|Press the .*button\.?$|^Invoke the', t, re.I) and len(t) < 160 and 'invoke' in t.lower():
            continue
        if re.fullmatch(r'(There are .*ways.*|Press the <b>.*</b> button\.?|Select the <b>.*</b> option from the menu\.?)', t):
            continue
        if len(t) > 220:
            t = t[:217].rsplit(' ', 1)[0] + '…'
        if len(re.sub(r'<[^>]+>|\\W', '', t)) < 6:
            continue
        steps.append(t)
        if len(steps) >= maxn:
            break
    return steps

data = {}; images = set()
for fn in sorted(os.listdir(WIKI)):
    if not fn.endswith('.md'):
        continue
    text = open(os.path.join(WIKI, fn), encoding='utf-8', errors='replace').read()
    if not re.search(r'^ GuiCommand:', text, re.M):
        continue
    name = fn[:-3]
    title = re.search(r'^# (.+)$', text, re.M)
    menu = re.search(r'^\s+MenuLocation:\s*(.+)$', text, re.M)
    sc = re.search(r'^\s+Shortcut:\s*(.+)$', text, re.M)
    ver = re.search(r'^\s+Version:\s*(.+)$', text, re.M)
    desc_block = section(text, 'Description')
    use_block = section(text, 'Usage')
    if not desc_block.strip():
        # pages without heading: text after the title
        m = re.search(r'^# .+$(.*?)(?=^## |\Z)', text, re.M | re.S)
        desc_block = m.group(1) if m else ''
    img = pick_image(desc_block, name) or pick_image(use_block, name) or pick_image(text, name)
    d = paragraphs(desc_block)
    if not d and not img:
        continue
    entry = {'t': title.group(1).strip() if title else name.replace('_', ' '),
             'd': d, 'u': usage_steps(use_block)}
    if menu: entry['m'] = ' → '.join(x for x in (strip_inline(part) for part in menu.group(1).split(' , ')) if x)
    if sc: entry['k'] = strip_inline(sc.group(1))
    if ver: entry['v'] = ver.group(1).strip()
    if img:
        entry['i'] = img; images.add(img)
    data[name] = entry

json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
open(OUT + '.images.txt', 'w').write('\n'.join(sorted(images)))
print(len(data), 'commands,', len(images), 'images')
