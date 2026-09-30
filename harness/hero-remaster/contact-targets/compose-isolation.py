"""Pixel-only layout of genuine CPU source renders; no image generation or retouching."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
root, out = Path(args.input), Path(args.output)
out.mkdir(parents=True, exist_ok=True)
for bike in ['rookie', 'pro']:
    canvas = Image.new('RGB', (1280, 840), '#20252d')
    draw = ImageDraw.Draw(canvas)
    for row, detail in enumerate(['full', 'lod']):
        for col, mode in enumerate(['pbr', 'gray']):
            file = root/f'render-{bike}-{detail}-lowlight'/f'{mode}.png'
            render = Image.open(file).convert('RGB')
            assert render.size == (640, 384)
            canvas.paste(render, (col*640, row*420+36))
            draw.text((col*640+12, row*420+11), f'{bike.upper()} {detail.upper()} — SOURCE {mode.upper()} — no rider/contact acceptance', fill='#eeeeee')
    canvas.save(out/f'{bike}-source-grips.jpg', quality=94)
