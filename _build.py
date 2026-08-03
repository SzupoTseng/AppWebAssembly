#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""組裝《幽靈組語》成品:
  1) 合併單一 Markdown 檔  幽靈組語_全書.md
  2) 圖文 HTML(側邊子目錄)  幽靈組語.html
版面沿用系列標準 _build.py(同一套 CSS / 解析器),
內容為技術評註書(WebAssembly、靜態託管與後護城河時代的工程實錄)。
用法: python3 _build.py
"""
import os, re, glob, html, base64

BOOK = os.path.dirname(os.path.abspath(__file__))

BOOK_TITLE = "幽靈組語"
BOOK_SUB   = "WebAssembly、靜態託管與後護城河時代的工程實錄 · Ghost Assembly"
COVER_CANDIDATES = ["GhostAssembly.png", "幽靈組語.png", "cover.png"]

def cover_path():
    for c in COVER_CANDIDATES:
        p = os.path.join(BOOK, c)
        if os.path.exists(p):
            return p
    return None

# ---- 章節檔順序: 00_序言 → NN_*.md(1..49) → 附錄_* ----
def order():
    fs = []
    pre = glob.glob(os.path.join(BOOK, "00_*.md"))
    if pre: fs.append(os.path.basename(pre[0]))
    for n in range(1, 50):
        cand = glob.glob(os.path.join(BOOK, f"{n:02d}_*.md"))
        if cand: fs.append(os.path.basename(cand[0]))
    for apx in sorted(glob.glob(os.path.join(BOOK, "附錄*_*.md"))):
        fs.append(os.path.basename(apx))
    return fs

FILES = order()

def anchor_for(base):
    if base.startswith("00_"): return "fm"
    m = re.match(r'(\d{2})_', base)
    if m: return f"ch{m.group(1)}"
    return "apx" + re.sub(r'\W+', '', base)[:4]

def title_for(base, text):
    if base.startswith("00_"):
        m = re.search(r'^##\s+(序.*)$', text, re.M)
        return m.group(1).strip() if m else "序言"
    m = re.search(r'^#\s+(第\s*\d+\s*章[　 ].*)$', text, re.M)
    if m: return m.group(1).strip()
    m = re.search(r'^#\s+(附錄.*)$', text, re.M)
    return m.group(1).strip() if m else base

def part_for(text):
    m = re.search(r'^#\s+(第.篇[　 ].*)$', text, re.M)
    return m.group(1).strip() if m else None

# ============ 1) 合併單一 Markdown ============
def build_merged():
    parts = []
    parts.append(f"# 《{BOOK_TITLE}》\n### ——{BOOK_SUB}\n")
    cp = cover_path()
    if cp:
        parts.append(f"![{BOOK_TITLE} — 封面海報]({os.path.basename(cp)})\n")
    parts.append("> 全書合併版。本書為教育與研究用途，橫跨 WebAssembly 的執行機制、靜態託管落地"
                 "與後護城河時代商業結構三大主題的整理與批判性評註。\n")
    parts.append("\n---\n\n## 目錄\n")
    for base in FILES:
        text = open(os.path.join(BOOK, base), encoding="utf-8").read()
        p = part_for(text); t = title_for(base, text)
        if p: parts.append(f"\n**{p}**\n")
        parts.append(f"- {t}")
    parts.append("\n\n---\n")
    for base in FILES:
        text = open(os.path.join(BOOK, base), encoding="utf-8").read().rstrip()
        parts.append("\n\n" + text + "\n\n---\n")
    out = os.path.join(BOOK, f"{BOOK_TITLE}_全書.md")
    open(out, "w", encoding="utf-8").write("\n".join(parts))
    return out

# ============ 極簡 Markdown → HTML(對應本書語法子集) ============
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t

def svg_or_img(path, alt, tile=False):
    desc = re.sub(r'^概念圖[:：]\s*', '', alt)
    cls = "tile" if tile else "plate"
    full = os.path.join(BOOK, path)
    ext = os.path.splitext(full)[1].lower()
    if os.path.exists(full) and ext in (".jpg", ".jpeg", ".png", ".gif"):
        data = base64.b64encode(open(full, "rb").read()).decode()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext[1:]}"
        inner = f'<img src="data:{mime};base64,{data}" alt="{html.escape(desc)}"/>'
    else:
        inner = f'<img src="{html.escape(path)}" alt="{html.escape(desc)}"/>'
    return f'<figure class="{cls}">{inner}<figcaption>{html.escape(desc)}</figcaption></figure>'

def md_to_html(text):
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    fence = None
    while i < n:
        ln = lines[i]
        # 程式碼/ASCII 區塊 ```
        mf = re.match(r'^```(\w*)\s*$', ln)
        if mf:
            i += 1; buf = []
            while i < n and not re.match(r'^```\s*$', lines[i]):
                buf.append(lines[i]); i += 1
            i += 1
            code = html.escape("\n".join(buf), quote=False)
            out.append(f'<pre class="code"><code>{code}</code></pre>'); continue
        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', ln)
        if m:
            out.append(svg_or_img(m.group(2), m.group(1))); i += 1; continue
        if re.match(r'^---+\s*$', ln):
            out.append('<hr/>'); i += 1; continue
        m = re.match(r'^(#{1,4})\s+(.*)$', ln)
        if m:
            lvl = len(m.group(1)); out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>'); i += 1; continue
        if ln.startswith(">"):
            blk = []
            while i < n and lines[i].startswith(">"):
                blk.append(re.sub(r'^>\s?', '', lines[i])); i += 1
            if any("🔍" in b for b in blk):       # 進階點評框(藍綠)
                cls = "review"
            elif any(("🧠" in b or "💡" in b or "⚠️" in b) for b in blk):  # 觀念/提醒框(金)
                cls = "concept"
            else:
                cls = "quote"
            inner, buf = [], []
            def flush():
                if buf:
                    inner.append("<p>" + "<br/>".join(inline(x) for x in buf) + "</p>"); buf.clear()
            for b in blk:
                hm = re.match(r'^(#{1,4})\s+(.*)$', b)
                if hm:
                    flush(); inner.append(f'<p class="box-title">{inline(hm.group(2))}</p>')
                elif b.strip() == "":
                    flush()
                else:
                    buf.append(b)
            flush()
            out.append(f'<blockquote class="{cls}">' + "".join(inner) + '</blockquote>'); continue
        if ln.strip().startswith("|") and i + 1 < n and re.match(r'^\s*\|[\s:\-|]+\|\s*$', lines[i+1]):
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2; rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'); continue
        if re.match(r'^\s*\d+\.\s+', ln):
            items = []
            while i < n and re.match(r'^\s*\d+\.\s+', lines[i]):
                items.append(re.sub(r'^\s*\d+\.\s+', '', lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
        if re.match(r'^\s*[-*]\s+', ln):
            items = []
            while i < n and re.match(r'^\s*[-*]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*]\s+', '', lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"); continue
        if ln.strip() == "":
            i += 1; continue
        para = [ln]; i += 1
        while i < n and lines[i].strip() != "" and not re.match(r'^(#{1,4}\s|>|!\[|```|\s*[-*]\s|\s*\d+\.\s|---+\s*$|\s*\|)', lines[i]):
            para.append(lines[i]); i += 1
        out.append("<p>" + "<br/>".join(inline(x) for x in para) + "</p>")
    return "\n".join(out)

# ============ 2) HTML(側邊子目錄) ============
CSS = """
:root{--ink:#1d2230;--mut:#5a6378;--line:#e3e0d6;--pa:#fbf8f0;--accent:#9a3b2f;--accent2:#2f5d7a;--box:#fdf3e3;--boxln:#e8c88a}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:"Noto Serif CJK TC","Songti TC","PingFang TC","Microsoft JhengHei",serif;color:var(--ink);background:var(--pa);line-height:1.95;font-size:clamp(16.5px,2.7vw,18px);overflow-wrap:break-word}
#wrap{display:flex;align-items:flex-start}
#side{position:sticky;top:0;height:100vh;overflow-y:auto;width:300px;min-width:300px;background:#14182a;color:#cdd2e6;padding:26px 18px;font-family:"Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif;font-size:14px;line-height:1.6}
#side h1{font-size:22px;color:#f4b860;margin:0 0 4px;letter-spacing:4px}
#side .sub{color:#8b93b0;font-size:12px;margin-bottom:18px;line-height:1.5}
#side .part{color:#49c5e0;font-size:12px;margin:16px 0 6px;letter-spacing:1px;border-bottom:1px solid #2a3150;padding-bottom:4px}
#side a{display:block;color:#cdd2e6;text-decoration:none;padding:5px 8px;border-radius:6px}
#side a:hover{background:#222a45;color:#fff}
#side a.active{background:#2f3a60;color:#ffd98a}
main{flex:1;max-width:820px;margin:0 auto;padding:64px 56px 120px}
h1{font-size:30px;letter-spacing:2px;line-height:1.4;margin:8px 0 18px}
h1+h1{font-size:25px;color:var(--accent)}
h2{font-size:22px;margin:42px 0 14px;color:var(--accent);border-left:5px solid var(--accent);padding-left:12px}
h3{font-size:19px;margin:28px 0 10px}
h4{font-size:17px;margin:20px 0 8px;color:var(--accent2)}
p{margin:14px 0;text-align:justify}
strong{color:#111;font-weight:700;background:linear-gradient(transparent 62%,#ffe6a0 62%)}
code{background:#eee;padding:1px 5px;border-radius:4px;font-size:.9em}
pre.code{background:#14182a;color:#cdd2e6;padding:16px 18px;border-radius:10px;overflow-x:auto;font-size:13.5px;line-height:1.5;font-family:"DejaVu Sans Mono","Noto Sans Mono CJK TC","Consolas",monospace}
pre.code code{background:none;padding:0;color:inherit}
a{color:var(--accent2)}
hr{border:0;border-top:1px solid var(--line);margin:36px 0}
ul,ol{margin:14px 0;padding-left:24px}
li{margin:6px 0}
table{border-collapse:collapse;width:100%;margin:20px 0;font-size:15px;font-family:"Noto Sans CJK TC",sans-serif}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top;overflow-wrap:break-word}
th{background:#f0ebdd}
figure.plate{margin:30px 0;text-align:center}
figure.plate img{width:100%;max-width:760px;border-radius:10px;box-shadow:0 10px 30px rgba(20,24,42,.28)}
figcaption{font-size:13px;color:var(--mut);margin-top:10px;font-family:"Noto Sans CJK TC",sans-serif;line-height:1.6}
blockquote.quote{margin:22px 0;padding:14px 22px;border-left:4px solid var(--boxln);background:#faf4e6;color:#4a4334;font-style:normal}
blockquote.concept{margin:34px 0;padding:22px 26px;background:var(--box);border:1px solid var(--boxln);border-radius:14px;box-shadow:0 4px 14px rgba(180,140,60,.12)}
blockquote.concept .box-title{font-size:18px;font-weight:700;color:#9a6a1a;font-family:"Noto Sans CJK TC",sans-serif;margin:0 0 10px}
blockquote.concept p{margin:10px 0}
blockquote.review{margin:30px 0;padding:20px 24px;background:#eef5f7;border:1px solid #bcd6df;border-left:5px solid #2f5d7a;border-radius:12px;box-shadow:0 4px 14px rgba(47,93,122,.1)}
blockquote.review .box-title{font-size:17px;font-weight:700;color:#2f5d7a;font-family:"Noto Sans CJK TC",sans-serif;margin:0 0 10px}
blockquote.review p{margin:10px 0;font-size:16.5px;color:#274050}
section.chapter{padding-top:10px}
figure.cover{margin:0 0 10px;text-align:center}
figure.cover img{width:100%;max-width:680px;border-radius:12px;box-shadow:0 12px 36px rgba(20,24,42,.3)}
@page{size:A4;margin:16mm 17mm}
@media print{html,body{background:#fff;font-size:11.2pt;line-height:1.7}#side{display:none}main{max-width:100%;margin:0;padding:0}h1{font-size:20pt}h2{font-size:15pt;margin-top:22pt}h3{font-size:13pt}section.chapter{page-break-before:always}section.cover-page{page-break-before:avoid}figure.cover img{max-width:100%;box-shadow:none}h2,h3{break-after:avoid}table,figure,blockquote,pre{break-inside:avoid}blockquote.concept,blockquote.review{box-shadow:none}}
@media(max-width:780px){#side{display:none}main{padding:26px 16px}h1{font-size:24px}h2{font-size:19px}h3{font-size:17px}h4{font-size:15.5px}table{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}pre.code{font-size:12.5px}}
"""

JS = """
const links=[...document.querySelectorAll('#side a')];
const secs=links.map(a=>document.querySelector(a.getAttribute('href')));
const obs=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(l=>l.classList.remove('active'));const i=secs.indexOf(e.target);if(i>=0)links[i].classList.add('active');}})},{rootMargin:'-10% 0px -80% 0px'});
secs.forEach(s=>s&&obs.observe(s));
"""

def cover_section():
    p = cover_path()
    if not p: return "", ""
    data = base64.b64encode(open(p, "rb").read()).decode()
    fig = (f'<section class="chapter cover-page" id="cover">'
           f'<figure class="cover"><img src="data:image/png;base64,{data}" '
           f'alt="{html.escape(BOOK_TITLE)} — 封面海報"/></figure></section>')
    return '<a href="#cover">封面</a>', fig

def build_html():
    nav, body = [], []
    nav.append(f'<h1>{html.escape(BOOK_TITLE)}</h1><div class="sub">{html.escape(BOOK_SUB)}</div>')
    cnav, cbody = cover_section()
    if cbody: nav.append(cnav); body.append(cbody)
    for base in FILES:
        text = open(os.path.join(BOOK, base), encoding="utf-8").read()
        a = anchor_for(base); p = part_for(text); t = title_for(base, text)
        if p: nav.append(f'<div class="part">{html.escape(p)}</div>')
        nav.append(f'<a href="#{a}">{html.escape(t)}</a>')
        body.append(f'<section class="chapter" id="{a}">{md_to_html(text)}</section>')
    page = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(BOOK_TITLE)} — {html.escape(BOOK_SUB)}</title><style>{CSS}</style></head>
<body><div id="wrap"><nav id="side">{''.join(nav)}</nav><main>{''.join(body)}</main></div>
<script>{JS}</script></body></html>"""
    out = os.path.join(BOOK, f"{BOOK_TITLE}.html")
    open(out, "w", encoding="utf-8").write(page)
    return out

if __name__ == "__main__":
    m = build_merged(); print("合併單檔:", m, f"({os.path.getsize(m)//1024} KB)")
    h = build_html(); print("HTML:", h, f"({os.path.getsize(h)//1024} KB)")
