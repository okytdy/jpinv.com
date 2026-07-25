#!/usr/bin/env python3
"""Build the PROCESS / 進め方 flow diagram used on the service pages.

Renders a 4-step horizontal flow (desktop) plus a stacked variant (mobile),
each at 1x and 2x, in the site's own design language:
  ink #1a2a4a · rule #d6dee8 · bg-soft #fafbfc · accent (gold) #9a7838
Fonts: Noto Sans CJK JP (site uses Noto Sans JP), Noto Sans Mono CJK JP for the numerals.

Usage:  python3 tools/build_process_diagram.py
Writes: assets/diagrams/process_{key}_{lang}[_mobile][@2x].png

Text lives in STEPS below. Keep it identical to each page's alt text and the
visually-hidden <ol> fallback so screen readers and search engines still get it.
"""
from PIL import Image, ImageDraw, ImageFont

SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SANS_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
MONO = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
JP_IDX, MONO_IDX = 0, 5

INK = (26, 42, 74)
INK_SOFT = (48, 68, 102)
TEXT = (74, 85, 102)
RULE = (214, 222, 232)
BG_SOFT = (250, 251, 252)
GOLD = (154, 120, 56)
WHITE = (255, 255, 255)

STEPS = {
    ("disclosure", "ja"): [
        ("01", "お問い合わせ", "資料の種類、分量、開示予定時刻、希望納期をお知らせください。"),
        ("02", "範囲と納期の確認", "全文英訳、部分英訳、既存英訳レビュー、用語確認など、必要な範囲を整理します。"),
        ("03", "NDA・資料共有", "未公表情報を含む場合は、必要に応じてNDA締結後に資料を共有いただけます。"),
        ("04", "英訳・レビュー・納品", "数字、用語、定型表現、海外投資家への伝わり方を確認して納品します。"),
    ],
    ("disclosure", "en"): [
        ("01", "Inquiry", "Tell us the document type, volume, release time, and deadline."),
        ("02", "Scope and schedule", "We agree what needs full translation, partial translation, or review only."),
        ("03", "NDA and materials", "Where unreleased information is involved, materials are shared after an NDA."),
        ("04", "Translate, review, deliver", "Figures, terminology, and investor readability checked before delivery."),
    ],
}


def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def wrap(draw, text, fnt, max_w, lang):
    """Character wrapping for Japanese, word wrapping for English."""
    lines, cur = [], ""
    units = list(text) if lang == "ja" else text.split(" ")
    joiner = "" if lang == "ja" else " "
    no_lead = "。、）」・"  # never start a JP line with these
    for u in units:
        trial = cur + joiner + u if cur else u
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        elif lang == "ja" and u in no_lead:
            cur = trial  # allow slight overflow rather than orphan punctuation
        else:
            lines.append(cur)
            cur = u
    if cur:
        lines.append(cur)
    return lines


def arrow_h(draw, x0, x1, y, s):
    """Horizontal connector with a gold chevron head."""
    draw.line([(x0, y), (x1 - 5 * s, y)], fill=GOLD, width=max(1, int(1 * s)))
    draw.polygon(
        [(x1, y), (x1 - 7 * s, y - 4 * s), (x1 - 7 * s, y + 4 * s)], fill=GOLD
    )


def arrow_v(draw, x, y0, y1, s):
    draw.line([(x, y0), (x, y1 - 5 * s)], fill=GOLD, width=max(1, int(1 * s)))
    draw.polygon(
        [(x, y1), (x - 4 * s, y1 - 7 * s), (x + 4 * s, y1 - 7 * s)], fill=GOLD
    )


def build_desktop(steps, lang, s=2):
    W = 1000 * s
    gap = 36 * s
    card_w = (W - 3 * gap) // 4
    pad = 20 * s
    f_num = font(MONO, int(11 * s), MONO_IDX)
    f_title = font(SANS_BOLD, int(15 * s), JP_IDX)
    f_body = font(SANS, int(12.5 * s), JP_IDX)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    blocks = []
    for num, title, body in steps:
        tl = wrap(tmp, title, f_title, card_w - 2 * pad, lang)
        bl = wrap(tmp, body, f_body, card_w - 2 * pad, lang)
        blocks.append((num, tl, bl))
    title_lh, body_lh = int(24 * s), int(22 * s)
    card_h = max(
        pad + int(16 * s) + len(tl) * title_lh + int(8 * s) + len(bl) * body_lh + pad
        for _, tl, bl in blocks
    )
    H = card_h + 4 * s
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    for i, (num, tl, bl) in enumerate(blocks):
        x = i * (card_w + gap)
        d.rectangle([x, 0, x + card_w - 1, card_h - 1], fill=BG_SOFT, outline=RULE, width=max(1, int(1 * s)))
        d.rectangle([x, 0, x + int(2 * s), card_h - 1], fill=GOLD)  # accent edge
        y = pad
        d.text((x + pad, y), num, font=f_num, fill=GOLD)
        y += int(19 * s)
        for ln in tl:
            d.text((x + pad, y), ln, font=f_title, fill=INK)
            y += title_lh
        y += int(6 * s)
        for ln in bl:
            d.text((x + pad, y), ln, font=f_body, fill=TEXT)
            y += body_lh
        if i < 3:
            arrow_h(d, x + card_w + int(9 * s), x + card_w + gap - int(9 * s), card_h // 2, s)
    return img


def build_mobile(steps, lang, s=2):
    W = 380 * s
    pad = 18 * s
    gap = 30 * s
    f_num = font(MONO, int(11 * s), MONO_IDX)
    f_title = font(SANS_BOLD, int(15 * s), JP_IDX)
    f_body = font(SANS, int(12.5 * s), JP_IDX)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    blocks, heights = [], []
    for num, title, body in steps:
        tl = wrap(tmp, title, f_title, W - 2 * pad, lang)
        bl = wrap(tmp, body, f_body, W - 2 * pad, lang)
        blocks.append((num, tl, bl))
        heights.append(pad + int(19 * s) + len(tl) * int(24 * s) + int(6 * s) + len(bl) * int(22 * s) + pad)
    H = sum(heights) + 3 * gap
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    y0 = 0
    for i, ((num, tl, bl), ch) in enumerate(zip(blocks, heights)):
        d.rectangle([0, y0, W - 1, y0 + ch - 1], fill=BG_SOFT, outline=RULE, width=max(1, int(1 * s)))
        d.rectangle([0, y0, int(2 * s), y0 + ch - 1], fill=GOLD)
        y = y0 + pad
        d.text((pad, y), num, font=f_num, fill=GOLD)
        y += int(19 * s)
        for ln in tl:
            d.text((pad, y), ln, font=f_title, fill=INK)
            y += int(24 * s)
        y += int(6 * s)
        for ln in bl:
            d.text((pad, y), ln, font=f_body, fill=TEXT)
            y += int(22 * s)
        if i < len(blocks) - 1:
            arrow_v(d, W // 2, y0 + ch + int(8 * s), y0 + ch + gap - int(8 * s), s)
        y0 += ch + gap
    return img


def save_pair(img2x, out_base):
    img2x.save(f"{out_base}@2x.png", optimize=True)
    w, h = img2x.size
    img2x.resize((w // 2, h // 2), Image.LANCZOS).save(f"{out_base}.png", optimize=True)
    print("wrote", out_base + ".png", "+@2x", img2x.size)


if __name__ == "__main__":
    import os

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for (key, lang), steps in STEPS.items():
        save_pair(build_desktop(steps, lang), os.path.join(out_dir, f"process_{key}_{lang}"))
        save_pair(build_mobile(steps, lang), os.path.join(out_dir, f"process_{key}_{lang}_mobile"))
