# NFC Roon Controller - Display Feature (CRT Artwork)

Affichage en temps réel des pochettes d'album sur écran CRT connecté à Recalbox.

## Architecture

- **Pi 4** (192.168.1.60:5001) : Serveur Flask NFC + Roon API
- **Pi 5** (192.168.1.44) : Recalbox + scripts display
- **Écran CRT** : Sony PVM-14M2MDE (PAL 240p RGB)

### Flux de données

1. Carte NFC scannée → endpoint `/badge` (Pi 4)
2. Carte Display (UID: 0416FC8A3E6180) → crée flag `/tmp/display-now` via SSH
3. `roon-converter.sh` télécharge artwork de `/current-playing` toutes les 2s
4. `display-listener.sh` affiche artwork en boucle avec fbv
5. Rescanner Display → ferme affichage, redémarre Emulation Station

## Installation

### Prérequis Recalbox

- Pi 5 avec Recalbox 2023.02
- SSH activé (root sans password)
- ffmpeg, fbv, wget, curl, ffmpeg installés
- Emulation Station (lancé automatiquement)

### Setup SSH sans password (Pi 4 → Pi 5)

Sur **Pi 4** :

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@192.168.1.44
```

Test :
```bash
ssh root@192.168.1.44 "touch /tmp/test-ssh"
```

### Copier les scripts sur Recalbox

Sur **Pi 4** :

```bash
scp /path/to/roon-converter.sh root@192.168.1.44:/recalbox/share/nfc-roon-display/
scp /path/to/display-listener.sh root@192.168.1.44:/recalbox/share/nfc-roon-display/
```

Ou via SSH directement (voir fichiers fournis).

### Créer la structure

Sur **Recalbox** :

```bash
mkdir -p /recalbox/share/nfc-roon-display/cache
chmod +x /recalbox/share/nfc-roon-display/*.sh
```

### Configuration auto-démarrage

Fichier : `/recalbox/share/system/custom.sh`

```bash
#!/bin/bash
if [ "$1" = "start" ]; then
  nohup bash /recalbox/share/nfc-roon-display/roon-converter.sh > /tmp/roon-converter.log 2>&1 &
  nohup bash /recalbox/share/nfc-roon-display/display-listener.sh > /tmp/display-listener.log 2>&1 &
fi
```

## Utilisation

### Afficher l'artwork

Scannez la carte Display (UID: 0416FC8A3E6180).

L'artwork de la musique **actuellement en lecture** sur Roon s'affiche en plein écran.

L'affichage se met à jour automatiquement toutes les 2 secondes si la musique change.

### Fermer l'affichage

Rescannez la carte Display.

Emulation Station redémarre et reprend l'affichage normal.

## Configuration

### Modifier l'UID Display

Dans `serveur.py` (Pi 4), section mapping :

```json
"0416FC8A3E6180": {
  "action": "display",
  "title": "Display",
  "artist": "Show Now"
}
```

Remplacez `"0416FC8A3E6180"` par l'UID de votre carte.

### Ajuster la fréquence d'update

Dans `roon-converter.sh`, ligne `sleep 2` :

```bash
sleep 2  # Augmentez pour moins fréquent, diminuez pour plus fréquent
```

### Ajuster le timeout fbv

Dans `display-listener.sh`, ligne `timeout 1` :

```bash
timeout 1 fbv  # 1 seconde avant de relancer fbv (détecte changement faster)
```

## Troubleshooting

### L'image ne s'affiche pas

Vérifiez que :

1. Carte Display reconnue au scan (logs Pi 4) :
   ```bash
   sudo journalctl -u nfc-roon-server -f
   ```
   Doit afficher "Action: Display artwork"

2. Flag créé via SSH :
   ```bash
   ssh root@192.168.1.44 "ls -la /tmp/display-now"
   ```

3. Artwork généré :
   ```bash
   ssh root@192.168.1.44 "ls -la /recalbox/share/nfc-roon-display/cache/artwork.bmp"
   ```

4. Scripts tournent :
   ```bash
   ssh root@192.168.1.44 "ps aux | grep -E 'roon-converter|display-listener'"
   ```

### ES redémarre en boucle

Le script `display-listener.sh` bloque fbv avec `timeout`. Vérifiez que :

1. fbv est présent :
   ```bash
   ssh root@192.168.1.44 "which fbv"
   ```

2. `/dev/fb0` accessible :
   ```bash
   ssh root@192.168.1.44 "ls -la /dev/fb0"
   ```

3. Timeout est correctement configuré (doit être court, ex: 1 seconde)

### L'image est de mauvaise qualité

L'image est redimensionnée à 240x240 avec bandes noires (format 4/3 pour CRT PAL).

Pour ajuster :
- Dans `roon-converter.sh`, modifier `scale=240:240`
- Dans `roon-converter.sh`, modifier `pad=320:240` pour autre résolution CRT

### Logs

- **Converter** : `/tmp/roon-converter.log`
- **Listener** : `/tmp/display-listener.log`
- **Serveur NFC** : `sudo journalctl -u nfc-roon-server`

## Points de défaillance

1. **SSH sans password** : Réinitialiser si clé expirée
2. **Recalbox reboot** : `custom.sh` relance automatiquement les scripts
3. **Artwork manquant** : Roon API timeout ou image_url invalide
4. **fbv crash** : fbv ne supporte pas SDL2, doit utiliser framebuffer directement

## Fichiers

```
bonus/
├── DISPLAY.md (cette documentation)
└── recalbox/
    ├── roon-converter.sh (télécharge artworks)
    ├── display-listener.sh (affiche sur CRT)
    └── custom.sh (auto-démarrage Recalbox)
```

## Notes

- Feature secondaire, bonus par rapport au système NFC principal
- Testé sur Sony PVM-14M2MDE (PAL 240p)
- Peut être adapté à d'autres CRT ou écrans avec framebuffer
- Pas de dépendances externes au-delà de ffmpeg, fbv, wget, curl
