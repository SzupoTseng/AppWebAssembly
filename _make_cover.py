#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生《幽靈組語》封面海報（直式資訊圖，書名/副標/命題已燒進圖內）。
用法: python3 _make_cover.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1400, 2000
BG      = (18, 22, 42)
BG2     = (26, 32, 58)
INK     = (232, 236, 248)
MUT     = (140, 150, 180)
GOLD    = (244, 184, 96)
CYAN    = (73, 197, 224)
RED     = (226, 112, 92)
LINE    = (52, 62, 96)

CJK_BOLD  = "/mnt/c/Windows/Fonts/msjhbd.ttc"
CJK_REG   = "/mnt/c/Windows/Fonts/msjh.ttc"
CJK_LIGHT = "/mnt/c/Windows/Fonts/msjhl.ttc"
FALLBACK  = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
LATIN     = "/mnt/c/Windows/Fonts/arialbd.ttf"

def F(path, size, index=0):
    for p in (path, FALLBACK):
        try:
            return ImageFont.truetype(p, size, index=index)
        except Exception:
            continue
    return ImageFont.load_default()

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# ── 背景：垂直漸層 + 細網格 ────────────────────────────────
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)],
           fill=(int(18 + 12 * t), int(22 + 14 * t), int(42 + 20 * t)))
for x in range(0, W, 70):
    d.line([(x, 0), (x, H)], fill=(24, 30, 54))
for y in range(0, H, 70):
    d.line([(0, y), (W, y)], fill=(24, 30, 54))

M = 110  # 左右邊界

def center(text, font, y, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)
    return w

# ── 頂部標籤 ──────────────────────────────────────────────
f_tag = F(CJK_REG, 30)
d.line([(M, 150), (W - M, 150)], fill=LINE, width=2)
center("WebAssembly · 靜態託管 · 後護城河時代", f_tag, 178, MUT)

# ── 書名 ─────────────────────────────────────────────────
f_title = F(CJK_BOLD, 210)
center("幽靈組語", f_title, 250, INK)

f_en = F(LATIN, 40)
center("GHOST  ASSEMBLY", f_en, 498, GOLD)

f_sub = F(CJK_REG, 32)
center("那台不存在的機器，與它在每個分頁裡的沉默運轉", f_sub, 562, MUT)
center("WebAssembly、靜態託管與後護城河時代的工程實錄", F(CJK_REG, 27), 606, (110,120,150))

d.line([(W / 2 - 90, 664), (W / 2 + 90, 664)], fill=GOLD, width=3)

# ── 核心命題框 ────────────────────────────────────────────
bx0, by0, bx1, by1 = M, 700, W - M, 932
d.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=BG2, outline=GOLD, width=2)
f_lbl = F(CJK_BOLD, 28)
d.text((bx0 + 42, by0 + 34), "核心命題", font=f_lbl, fill=GOLD)
f_q = F(CJK_BOLD, 46)
center("能被下載的，遲早會被複製；", f_q, by0 + 92, INK)
center("不能被搬走的，才是護城河。", f_q, by0 + 158, INK)

# ── 三個樂章 ─────────────────────────────────────────────
f_mv_no = F(LATIN, 26)
f_mv_cn = F(CJK_BOLD, 54)
f_mv_ds = F(CJK_REG, 26)

movements = [
    ("I",   "懂它", CYAN, "第 1–4 章", "二進位的物理學", "堆疊機器 · 線性記憶體", "Wasm 3.0 · 六場競爭"),
    ("II",  "用它", GOLD, "第 5–8 章", "在靜態頁上造機器", "COOP/COEP · 101 案圖鑑", "OPFS 儲存 · 4GB 天花板"),
    ("III", "守它", RED,  "第 9–12 章", "看光之後的護城河", "天然混淆 · Figma 四道防線", "技術商品化 · Token 歸零"),
]
top = 970
colw = (W - 2 * M) // 3
for i, (no, cn, color, chs, t1, t2, t3) in enumerate(movements):
    cx = M + colw * i + colw // 2
    d.line([(M + colw * i + 26, top), (M + colw * (i + 1) - 26, top)], fill=color, width=3)
    w = d.textlength(no, font=f_mv_no); d.text((cx - w / 2, top + 26), no, font=f_mv_no, fill=color)
    w = d.textlength(cn, font=f_mv_cn); d.text((cx - w / 2, top + 66), cn, font=f_mv_cn, fill=INK)
    w = d.textlength(chs, font=f_mv_ds); d.text((cx - w / 2, top + 146), chs, font=f_mv_ds, fill=color)
    for j, tx in enumerate((t1, t2, t3)):
        w = d.textlength(tx, font=f_mv_ds)
        d.text((cx - w / 2, top + 196 + j * 40), tx, font=f_mv_ds, fill=MUT)

# ── 中段分隔 ─────────────────────────────────────────────
d.line([(M, 1360), (W - M, 1360)], fill=LINE, width=2)

# ── 那條分界線示意圖 ──────────────────────────────────────
f_dg_t = F(CJK_BOLD, 32)
f_dg   = F(CJK_REG, 27)
center("那條唯一重要的線", f_dg_t, 1400, GOLD)

# 上盒：客戶端
d.rounded_rectangle([M, 1470, W - M, 1620], radius=14, fill=(30, 38, 66), outline=CYAN, width=2)
d.text((M + 40, 1494), "客戶端 Wasm　—　重、公開、無機密", font=f_dg_t, fill=CYAN)
d.text((M + 40, 1546), "影音轉碼 · 幾何求解 · 本地查詢 · 邊緣推理", font=f_dg, fill=MUT)
d.text((M + 40, 1582), "免費、無限並發、資料不離端　→　可以被完整下載", font=f_dg, fill=MUT)

# 中間箭頭
d.line([(W / 2, 1626), (W / 2, 1664)], fill=GOLD, width=3)
d.polygon([(W / 2 - 10, 1660), (W / 2 + 10, 1660), (W / 2, 1678)], fill=GOLD)

# 下盒：伺服器端
d.rounded_rectangle([M, 1686, W - M, 1836], radius=14, fill=(44, 30, 40), outline=RED, width=2)
d.text((M + 40, 1710), "伺服器端　—　輕、機密、決定價值", font=f_dg_t, fill=RED)
d.text((M + 40, 1762), "鑑權 · 金鑰 · 計費 · 協作仲裁 · 資料所有權", font=f_dg, fill=MUT)
d.text((M + 40, 1798), "運算量小、洩漏即災難　→　永遠不下載", font=f_dg, fill=MUT)

# ── 底部規模 ─────────────────────────────────────────────
d.line([(M, 1888), (W - M, 1888)], fill=LINE, width=2)
f_ft = F(CJK_REG, 28)
center("正文 12 章　·　附錄 A–O　·　百案圖鑑 101 案　·　規範深水區　·　體積與速度　·　測試與 CI", f_ft, 1914, MUT)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GhostAssembly.png")
img.save(out, "PNG", optimize=True)
print("cover:", out, os.path.getsize(out) // 1024, "KB")
