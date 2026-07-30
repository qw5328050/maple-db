"""Annotate map entrance images with portal location markers."""
from PIL import Image, ImageDraw, ImageFont
import os

PROJECT = r'D:\tools\project\maple-db'
ENTRANCE_DIR = os.path.join(PROJECT, 'images', 'entrances')
os.makedirs(ENTRANCE_DIR, exist_ok=True)

# Key entrances to annotate
# Each: (parent_image_webp, output_png, portals[(game_x, game_y, label, color)])
entrances = [
    {
        'src': os.path.join(ENTRANCE_DIR, 'parent_10000020.webp'),
        'dst': os.path.join(ENTRANCE_DIR, 'to_10000021.png'),
        'image_size': (1900, 1002),
        'title': '猪的海岸 入口',
        'portals': [
            (43, -206, '按↑进入\n猪的海岸', 'red'),
            (1063, -380, '按↑进入\n海滩狩猎场', 'orange'),
        ],
    },
]

try:
    font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 16)
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 22)
    print("Using MS YaHei font")
except:
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\simhei.ttf", 16)
        font_title = ImageFont.truetype("C:\\Windows\\Fonts\\simhei.ttf", 22)
    except:
        font = ImageFont.load_default()
        font_title = ImageFont.load_default()

for ent in entrances:
    img = Image.open(ent['src'])
    w, h = ent['image_size']
    cx, cy = w / 2, h / 2
    
    draw = ImageDraw.Draw(img)
    
    # Draw title
    draw.text((10, 10), ent['title'], fill='yellow', font=font_title, 
              stroke_width=2, stroke_fill='black')
    
    for (gx, gy, label, color) in ent['portals']:
        # Convert game coords to image coords
        # Game (0,0) = center of image
        # img_x = center_x + game_x, img_y = center_y - game_y
        px = int(cx + gx)
        py = int(cy - gy)
        
        r = 35
        # Draw circle
        draw.ellipse([px-r, py-r, px+r, py+r], outline=color, width=4)
        # Draw crosshair
        draw.line([px-15, py, px+15, py], fill=color, width=2)
        draw.line([px, py-15, px, py+15], fill=color, width=2)
        # Draw arrow from top-left
        ax, ay = px - 60, py - 60
        draw.line([ax, ay, px-15, py-15], fill=color, width=3)
        
        # Draw label text with background
        lines = label.split('\n')
        text_h = len(lines) * 20 + 4
        text_w = max(len(l) * 12 for l in lines) + 10
        label_x = px + 45
        label_y = py - text_h // 2
        draw.rectangle([label_x-3, label_y-3, label_x+text_w, label_y+text_h], 
                       fill='black')
        for i, line in enumerate(lines):
            draw.text((label_x, label_y + i*20), line, fill=color, font=font)
    
    img.save(ent['dst'], 'PNG')
    print(f"Saved: {ent['dst']} ({os.path.getsize(ent['dst'])} bytes)")

print("\nDone!")
