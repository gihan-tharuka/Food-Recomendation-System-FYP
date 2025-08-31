from PIL import Image, ImageDraw
import os

# Create a 32x32 image for favicon
img = Image.new('RGB', (32, 32), color='white')
draw = ImageDraw.Draw(img)

# Draw a simple plate with food
# Outer circle (plate rim)
draw.ellipse([2, 2, 30, 30], fill='#FF6B35', outline='#2C1810', width=2)
# Inner circle (plate)
draw.ellipse([6, 8, 26, 28], fill='#FFF', outline='#D4AF37', width=1)
# Food items (simple dots)
draw.ellipse([11, 14, 15, 18], fill='#FF4757')  # Red food
draw.ellipse([17, 14, 21, 18], fill='#4ECDC4')  # Green food
draw.ellipse([14, 20, 18, 24], fill='#FFE66D')  # Yellow food

# Save as ICO
img.save('favicon.ico', format='ICO', sizes=[(16,16), (32,32)])
print("Favicon created successfully!")
