#!/usr/bin/env python3
"""
Kindle Display Module - Affiche pochette et infos album sur Kindle PW1
Pour intégration avec NFC Roon Controller
"""

import subprocess
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Configuration Kindle
KINDLE_IP = "192.168.1.63"
KINDLE_USER = "root"

# Dimensions natives du Kindle (Touch/K5)
KINDLE_WIDTH = 600
KINDLE_HEIGHT = 800

# Chemins sur le Kindle
KINDLE_IMAGE_PATH = "/mnt/us/display.png"


def create_display_image(cover_url=None, album="", artist="", year="", track=""):
    """
    Crée une image pour le Kindle avec pochette et infos

    Args:
        cover_url: URL de la pochette (ou None pour placeholder)
        album: Nom de l'album
        artist: Nom de l'artiste
        year: Année de sortie
        track: Titre du morceau en cours

    Returns:
        PIL.Image en niveaux de gris 600x800
    """
    # Image de base en niveaux de gris
    img = Image.new('L', (KINDLE_WIDTH, KINDLE_HEIGHT), color=255)
    draw = ImageDraw.Draw(img)

    # Zone pochette (carrée, centrée en haut)
    cover_size = 480
    cover_x = (KINDLE_WIDTH - cover_size) // 2
    cover_y = 20

    # Charger la pochette
    if cover_url:
        try:
            response = requests.get(cover_url, timeout=10)
            cover = Image.open(BytesIO(response.content))
            cover = cover.convert('L')  # Niveaux de gris
            cover = cover.resize((cover_size, cover_size), Image.Resampling.LANCZOS)
            img.paste(cover, (cover_x, cover_y))
        except Exception as e:
            # Placeholder si erreur
            draw.rectangle([cover_x, cover_y, cover_x + cover_size, cover_y + cover_size],
                           outline=0, width=2)
            draw.text((cover_x + 160, cover_y + 220), "No Cover", fill=128)
    else:
        # Placeholder
        draw.rectangle([cover_x, cover_y, cover_x + cover_size, cover_y + cover_size],
                       outline=0, width=2)

    # Polices
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # Position du texte (sous la pochette)
    text_x = 30
    text_y = cover_y + cover_size + 20
    max_width = KINDLE_WIDTH - 60

    # Album (gras)
    if album:
        album_text = truncate_text(album, font_large, max_width, draw)
        draw.text((text_x, text_y), album_text, font=font_large, fill=0)
        text_y += 36

    # Artiste + Année sur la même ligne
    info_line = artist
    if year:
        info_line += f" ({year})"
    if info_line:
        info_text = truncate_text(info_line, font_medium, max_width, draw)
        draw.text((text_x, text_y), info_text, font=font_medium, fill=60)
        text_y += 32

    # Séparateur
    text_y += 5
    draw.line([(text_x, text_y), (KINDLE_WIDTH - text_x, text_y)], fill=180, width=1)
    text_y += 15

    # Morceau en cours
    if track:
        draw.text((text_x, text_y), "En cours:", font=font_small, fill=100)
        text_y += 24
        track_text = truncate_text(track, font_medium, max_width, draw)
        draw.text((text_x, text_y), track_text, font=font_medium, fill=0)

    return img


def truncate_text(text, font, max_width, draw):
    """Tronque le texte avec ... si trop long"""
    if draw.textlength(text, font=font) <= max_width:
        return text

    while draw.textlength(text + "...", font=font) > max_width and len(text) > 0:
        text = text[:-1]

    return text + "..."


def send_to_kindle(image, kindle_ip=KINDLE_IP):
    """
    Envoie l'image au Kindle et l'affiche

    Args:
        image: PIL.Image ou chemin vers fichier PNG
        kindle_ip: Adresse IP du Kindle
    """
    # Sauvegarder temporairement si c'est une image PIL
    if isinstance(image, Image.Image):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            image.save(temp_path, 'PNG')
    else:
        temp_path = image

    try:
        # Copier l'image sur le Kindle
        subprocess.run([
            'scp', '-o', 'StrictHostKeyChecking=no',
            temp_path,
            f'{KINDLE_USER}@{kindle_ip}:{KINDLE_IMAGE_PATH}'
        ], check=True, capture_output=True)

        # Désactiver la veille + afficher l'image
        subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no',
            f'{KINDLE_USER}@{kindle_ip}',
            f'lipc-set-prop com.lab126.powerd preventScreenSaver 1; eips -c; eips -g {KINDLE_IMAGE_PATH}'
        ], check=True, capture_output=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Erreur Kindle: {e}")
        return False

    finally:
        # Nettoyer le fichier temporaire
        if isinstance(image, Image.Image) and os.path.exists(temp_path):
            os.unlink(temp_path)


def update_kindle_display(cover_url=None, album="", artist="", year="", track="", kindle_ip=KINDLE_IP):
    """
    Fonction principale - crée et envoie l'affichage au Kindle

    Args:
        cover_url: URL de la pochette
        album: Nom de l'album
        artist: Nom de l'artiste
        year: Année
        track: Morceau en cours
        kindle_ip: IP du Kindle

    Returns:
        bool: True si succès
    """
    img = create_display_image(cover_url, album, artist, year, track)
    return send_to_kindle(img, kindle_ip)


def clear_kindle_display(kindle_ip=KINDLE_IP):
    """Efface l'écran du Kindle"""
    try:
        subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no',
            f'{KINDLE_USER}@{kindle_ip}',
            'eips -c'
        ], check=True, capture_output=True)
        return True
    except:
        return False


# Test
if __name__ == "__main__":
    # Test avec des données fictives
    print("Test d'affichage Kindle...")

    success = update_kindle_display(
        cover_url=None,  # Pas de pochette pour le test
        album="Album Test",
        artist="Artiste Test",
        year="2024",
        track="Morceau en cours de lecture"
    )

    if success:
        print("✓ Image envoyée au Kindle")
    else:
        print("✗ Erreur lors de l'envoi")