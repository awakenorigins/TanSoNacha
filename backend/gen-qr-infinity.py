#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh QR Phước Phiếu có dấu VÔ CỰC ∞ ở giữa (theo mẫu anh Nấng).
- Module bo tròn (rounded), màu ink #2C2C2C trên nền trắng.
- Vòng tròn trắng giữa + ký hiệu ∞ nét mảnh.
Đọc danh sách code từ SQLite vouchers, xuất PNG vào vouchers-out/<pham>/.
Chạy: venv/bin/python gen-qr-infinity.py
"""
import sqlite3, os, math
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'data', 'phuocphieu.db')
OUT = os.path.join(BASE, 'vouchers-out')
SHLINK = 'https://qr.62.146.238.213.sslip.io'

INK = (44, 44, 44)      # #2C2C2C
WHITE = (255, 255, 255)

def make_infinity_logo(size):
    """Vòng tròn trắng + ký hiệu ∞ LIỀN NÉT (lemniscate) — vẽ bằng nhiều điểm dậy nét tròn."""
    SS = 4  # supersample cho mượt
    S = size * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # vòng tròn trắng nền
    d.ellipse([0, 0, S-1, S-1], fill=WHITE + (255,))
    # đường lemniscate of Gerono: x = a*cos t ; y = a*sin t*cos t
    cx, cy = S/2, S/2
    a = S * 0.30
    lw = max(2, int(S * 0.052))
    pts = []
    steps = 240
    for i in range(steps + 1):
        t = (i / steps) * 2 * math.pi
        x = cx + a * math.cos(t)
        y = cy + a * math.sin(t) * math.cos(t)
        pts.append((x, y))
    d.line(pts, fill=INK + (255,), width=lw, joint='curve')
    # bọc đầu nối cho mượt
    r = lw / 2
    for (x, y) in (pts[0], pts[-1]):
        d.ellipse([x-r, y-r, x+r, y+r], fill=INK + (255,))
    img = img.resize((size, size), Image.LANCZOS)
    return img

def gen_one(code, out_path):
    url = f'{SHLINK}/{code}'
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # H = chịu che logo tốt
        box_size=14, border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(front_color=INK, back_color=WHITE),
    ).convert('RGBA')

    W, H = img.size
    logo_size = int(W * 0.22)
    logo = make_infinity_logo(logo_size)
    pos = ((W - logo_size) // 2, (H - logo_size) // 2)
    img.alpha_composite(logo, pos)
    img.convert('RGB').save(out_path, 'PNG')

def main():
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT code, pham FROM vouchers ORDER BY prefix, seq").fetchall()
    con.close()
    n = 0
    for code, pham in rows:
        d = os.path.join(OUT, pham)
        os.makedirs(d, exist_ok=True)
        gen_one(code, os.path.join(d, f'{code}.png'))
        n += 1
        if n % 100 == 0:
            print(f'  ...{n}/{len(rows)}')
    print(f'DONE {n} QR ∞')

if __name__ == '__main__':
    main()
