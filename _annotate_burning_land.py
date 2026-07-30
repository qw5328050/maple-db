import urllib.request
from PIL import Image, ImageDraw, ImageFont
import os

# Download the map image
url = "https://www.longlegmxd.com/wp-content/plugins/map-navigator/mapres/106000100.webp"
img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "entrances")
os.makedirs(img_dir, exist_ok=True)
img_path = os.path.join(img_dir, "parent_10004110.webp")

req = urllib.request.Request(url)
req.add_header("User-Agent", "Mozilla/5.0")
with urllib.request.urlopen(req, timeout=30) as resp:
    with open(img_path, "wb") as f:
        f.write(resp.read())
print(f"Downloaded: {img_path} ({os.path.getsize(img_path)} bytes)")

# Portal in00: game(-116, 1377)
# miniMap: centerX=874, centerY=-559, mag=4, canvasWidth=155, canvasHeight=109
# imageWidth=930, imageHeight=654
scale = 2 ** 4
centerX, centerY = 874, -559
canvasW, canvasH = 155, 109
imgW, imgH = 930, 654

game_x, game_y = -116, 1377
canvas_x = (game_x + centerX) / scale
canvas_y = (game_y + centerY) / scale
pixel_x = canvas_x * (imgW / canvasW)
pixel_y = canvas_y * (imgH / canvasH)
print(f"Portal pixel: ({pixel_x:.1f}, {pixel_y:.1f}) on {imgW}x{imgH}")

# Annotate
img = Image.open(img_path).convert("RGBA")
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

r = 28
cx, cy = int(pixel_x), int(pixel_y)

for i in range(3):
    draw.ellipse([cx - r - i*4, cy - r - i*4, cx + r + i*4, cy + r + i*4],
                 outline=(233, 69, 96, 180 - i*40), width=2)
draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(233, 69, 96, 255), width=3)
draw.line([cx, cy + r, cx, cy + r + 25], fill=(233, 69, 96, 200), width=3)
draw.polygon([(cx-8, cy+r+15), (cx, cy+r+30), (cx+8, cy+r+15)], fill=(233, 69, 96, 200))

try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)
    cfont = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 12)
except:
    font = ImageFont.load_default()
    cfont = font

label = "燃烧之地 I 入口"
bbox = draw.textbbox((0, 0), label, font=font)
tx = cx - bbox[2] // 2
ty = cy + r + 35
draw.rectangle([tx - 6, ty - 4, tx + bbox[2] + 6, ty + bbox[3] + 4], fill=(0, 0, 0, 180))
draw.text((tx, ty), label, fill=(245, 197, 24, 255), font=font)

credit = "map src: longlegmxd.com"
cbbox = draw.textbbox((0, 0), credit, font=cfont)
draw.rectangle([imgW - cbbox[2] - 12, imgH - cbbox[3] - 10, imgW - 4, imgH - 4], fill=(0, 0, 0, 140))
draw.text((imgW - cbbox[2] - 8, imgH - cbbox[3] - 8), credit, fill=(160, 160, 180, 200), font=cfont)

result = Image.alpha_composite(img, overlay)
output_path = os.path.join(img_dir, "to_10004111.png")
result.save(output_path, "PNG")
print(f"Saved: {output_path}")
