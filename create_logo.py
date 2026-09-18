from PIL import Image, ImageDraw, ImageFont
import os

# Créer une image de 200x200 pixels avec un fond blanc
width, height = 200, 200
image = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(image)

# Dessiner un rectangle bleu
draw.rectangle([(20, 20), (180, 180)], fill='blue', outline='blue')

# Dessiner un cercle jaune au centre
draw.ellipse([(50, 50), (150, 150)], fill='yellow', outline='yellow')

# Ajouter du texte
try:
    # Essayer de charger une police
    font = ImageFont.truetype("arial.ttf", 20)
    draw.text((60, 90), "FLEET", fill='black', font=font)
except IOError:
    # Si la police n'est pas disponible, utiliser la police par défaut
    draw.text((60, 90), "FLEET", fill='black')

# Sauvegarder l'image
logo_path = os.path.join('static', 'images', 'logo.png')
image.save(logo_path)

print(f"Logo créé avec succès à {logo_path}")
