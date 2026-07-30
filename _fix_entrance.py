"""Annotate 三岔路口 map with corrected portal positions for hidden entrances.

Coordinate conversion (from longlegmxd app.js):
  scale = 2^mag = 16
  canvas_x = (game_x + centerX) / scale = (game_x + 1790) / 16
  canvas_y = (game_y + centerY) / scale = (game_y + 2018) / 16
  pixel_x = canvas_x * (imageWidth / canvasWidth) = canvas_x * (1900/326)
  pixel_y = canvas_y * (imageHeight / canvasHeight) = canvas_y * (1002/172)
"""
from PIL import Image, ImageDraw, ImageFont
import os

PROJECT = r'D:\tools\project\maple-db'
SRC = os.path.join(PROJECT, 'images', 'entrances', 'parent_10000020.webp')
DST = os.path.join(PROJECT, 'images', 'entrances', 'to_10000021.png')

# MiniMap data for 三叉路 (104010000)
CENTER_X, CENTER_Y = 1790, 2018
MAG = 4  # scale = 2^4 = 16
CANVAS_W, CANVAS_H = 326, 172
IMG_W, IMG_H = 1900, 1002

scale = 2 ** MAG  # 16

def game_to_pixel(gx, gy):
    """Convert game coords to image pixel coords."""
    cx = (gx + CENTER_X) / scale
    cy = (gy + CENTER_Y) / scale
    px = cx * (IMG_W / CANVAS_W)
    py = cy * (IMG_H / CANVAS_H)
    return int(px), int(py)

# Portals to Pig Beach (104010001)
# h_in00: (43, -206) - main entrance
# h_out00: (1063, -380) - secondary entrance
portals = [
    (43, -206, '→ 猪的海岸\n按↑键进入', '#ff3333'),
    (1063, -380, '→ 海滩狩猎场\n按↑键进入', '#ff9933'),
]

img = Image.open(SRC).convert('RGBA')

# Create an overlay layer for annotations (so we can draw without modifying original pixels)
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

try:
    font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 16)
    font_big = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 22)
except:
    font = ImageFont.load_default()
    font_big = ImageFont.load_default()

# Watermark: cover the longlegmxd.com text by drawing semi-transparent 
# black rectangles over the background sky area
# The watermark "longlegmxd.com" is repeated diagonally - we can't fully remove it
# But we put our own label credit

# Draw title bar at top
draw.rectangle([0, 0, IMG_W, 36], fill=(0, 0, 0, 200))
draw.text((10, 6), '三岔路口 → 隐藏地图入口', fill='#ffdd00', font=font_big)

for (gx, gy, label, color) in portals:
    px, py = game_to_pixel(gx, gy)
    print(f"Portal at game({gx},{gy}) -> pixel({px},{py})")
    
    r = 30
    # Outer glow
    for glow_r in range(r+15, r+5, -1):
        alpha = int(80 * (glow_r - r) / 15)
        draw.ellipse([px-glow_r, py-glow_r, px+glow_r, py+glow_r], 
                     outline=(255, 60, 60, alpha), width=2)
    
    # Main circle
    draw.ellipse([px-r, py-r, px+r, py+r], outline=color, width=4)
    
    # Animated-style arrow pointing at portal
    arrow_angle = -30  # degrees
    import math
    ax1 = px + int(80 * math.cos(math.radians(arrow_angle + 90)))
    ay1 = py - int(80 * math.sin(math.radians(arrow_angle + 90)))
    ax2 = px + int(20 * math.cos(math.radians(arrow_angle + 90)))
    ay2 = py - int(20 * math.sin(math.radians(arrow_angle + 90)))
    
    draw.line([ax1, ay1, ax2, ay2], fill=color, width=3)
    # Arrowhead
    draw.line([ax1, ay1, ax1-8, ay1+8], fill=color, width=3)
    draw.line([ax1, ay1, ax1+8, ay1+8], fill=color, width=3)
    
    # Label background
    lines = label.split('\n')
    line_h = 22
    text_w = max(len(l) * 12 for l in lines) + 16
    text_h = len(lines) * line_h + 8
    
    # Position label to the right of the circle
    lx = px + r + 10
    ly = py - text_h // 2
    
    # Ensure label is within image bounds
    if lx + text_w > IMG_W:
        lx = px - r - text_w - 10
    if ly < 10:
        ly = 10
    if ly + text_h > IMG_H:
        ly = IMG_H - text_h - 10
    
    # Semi-transparent black background
    draw.rounded_rectangle([lx-4, ly-4, lx+text_w, ly+text_h], 
                           radius=6, fill=(0, 0, 0, 210))
    draw.rounded_rectangle([lx-4, ly-4, lx+text_w, ly+text_h], 
                           radius=6, outline=color, width=1)
    
    for i, line in enumerate(lines):
        draw.text((lx+2, ly+2 + i*line_h), line, fill=color, font=font)

# Composite overlay onto original
result = Image.alpha_composite(img, overlay)

# Add source credit at bottom-right
draw2 = ImageDraw.Draw(result)
draw2.text((IMG_W-230, IMG_H-22), '底图来源: longlegmxd.com', 
           fill=(150, 150, 150, 180), font=font)

result.save(DST, 'PNG')
print(f"\nSaved: {DST}")
print(f"Size: {os.path.getsize(DST)} bytes")
