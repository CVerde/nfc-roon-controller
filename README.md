# NFC Roon Controller

Control your music with NFC cards. Tap a card, and an album, playlist, or genre starts playing.

<img width="1664" height="1622" alt="Capture d’écran 2025-12-07 110127" src="https://github.com/user-attachments/assets/ccd759c9-eb42-4747-b92d-3c83fb57271a" />

## The project

The idea is to create a physical, tangible system to play music from my Roon server. Using a small Python server on a Raspberry Pi with an RFID reader, I built this little project that lets you start playing specific albums, playlists, or even genres. Some special cards can also change volume, pause/play, or toggle shuffle. In short, it's about controlling Roon with a deck of cards without using a phone or computer.

It works with any NFC card: building access badges, library cards, cafeteria cards, even contactless bank cards. Each card has a unique ID, you link it to an album and you're done.

## What you need

### Hardware

- **A USB NFC reader** — I use an ACR122U, it's the most common. Other PC/SC compatible readers should work too.
- **A Roon server** — With a local music library (no Qobuz/Tidal streaming for now)
- **A computer to run the server** — Windows, Linux, or a Raspberry Pi

### NFC Cards

Anything NFC/RFID will do:
- MIFARE cards
- Access badges
- Transit cards
- NFC stickers
- Old bank cards

## Installation

### On Windows

1. **Install Python 3.10+** from [python.org](https://python.org)

2. **Clone the project**
```bash
git clone https://github.com/CVerde/nfc-roon-controller.git
cd nfc-roon-controller
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run**
```bash
python serveur.py
```

In another terminal:
```bash
python nfc_reader.py
```

5. Open http://localhost:5000 in a browser

### On Raspberry Pi

1. **Install the system**

Raspberry Pi OS Lite is enough. After first boot:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git pcscd pcsc-tools
```

2. **Clone and install**
```bash
git clone https://github.com/CVerde/nfc-roon-controller.git
cd nfc-roon-controller
pip3 install -r requirements.txt --break-system-packages
```

3. **Check that the NFC reader is detected**
```bash
pcsc_scan
```
You should see your reader appear. Ctrl+C to quit.

4. **Set up autostart**
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nfc-roon-server nfc-roon-reader
sudo systemctl start nfc-roon-server nfc-roon-reader
```

5. Access the interface from another device: `http://PI_IP_ADDRESS:5000`

## Roon setup

On first launch, the system will try to connect to Roon. You need to authorize the extension:

1. Open Roon on your computer
2. Go to **Settings / Extensions**
3. You should see "NFC Roon Controller" — click **Enable**

The authorization token is automatically saved in `roon_token.json`.

## Usage

### Programming a card

1. Open the web interface (`http://localhost:5000` or `http://PI_IP_ADDRESS:5000`)
2. Scan a card on the reader — its ID appears
3. Search for an album in your library
4. Select and save

### Card types

- **Album** — Plays a specific album
- **Genre** — Plays random tracks from a genre
- **Playlist** — Plays a Roon playlist
- **Pause** — Pause / resume playback
- **Volume** — Sets volume to a specific level
- **Shuffle** — Toggle shuffle mode

### Choosing a zone

By default, music plays on the first available Roon zone. You can link a card to a specific zone in the interface.

### Display screen

A small bonus.
A `/display` page shows the cover art and current album info. Handy on a tablet or a dedicated old screen.
This page will later be updated to support e-ink displays.

## Project structure

```
nfc-roon-controller/
├── serveur.py          # Flask web server
├── nfc_reader.py       # NFC card reading
├── roon_controller.py  # Roon communication
├── config.py           # Configuration
├── utils.py            # Utility functions
├── templates/
│   ├── admin.html      # Admin interface
│   └── display.html    # Now playing display
├── systemd/            # Raspberry Pi services
└── scripts/            # Windows startup scripts
```

## Common issues

### NFC reader not detected

On Linux, check that `pcscd` is running:
```bash
sudo systemctl status pcscd
```

### Roon won't connect

- Check that Roon is running on the same network
- Delete `roon_token.json` and re-authorize
- Sometimes you just need to restart Roon...

### Cards aren't being read

Some badges have a very short range. Try placing the card flat on the reader. Bank cards usually work well. Library cards too. Door badges as well. But the best option is to buy blank PVC cards or rolls of stickers.

## Roadmap

- Streaming services support (Qobuz, Tidal)
- Pi Zero version with NFC HAT (more compact)
- Integration into furniture. Plans for 3D printing parts and enclosures
- E-ink display for always-on album art

## License

MIT

---

# Version française

Contrôler sa musique avec des cartes NFC. Une carte est posée, l'album, la playlist, un genre défini... se lance.

## Le projet

L'idée est de créer un système physique, tangible pour lancer de la musique depuis mon serveur Roon. Grâce à un petit serveur Python sur un Raspberry Pi avec un lecteur RFID, j'ai créé ce petit projet qui permet de lancer la lecture d'albums spécifiques, de playlists ou même de genres. Certaines cartes spéciales permettent même de changer le volume, de mettre pause/play, d'activer le shuffle. Pour résumer, il s'agit de contrôler Roon avec un deck de cartes sans utiliser de téléphone ou d'ordinateur.

Ça marche avec n'importe quelle carte NFC : badges d'immeuble, cartes de bibliothèque, de cantine, même les cartes bancaires (sans contact). Chaque carte a un identifiant unique, on l'associe à un album et voilà.

## Ce qu'il faut

### Matériel

- **Un lecteur NFC USB** — J'utilise un ACR122U, c'est le plus courant. D'autres modèles compatibles PC/SC devraient marcher aussi.
- **Un serveur Roon** — Avec une bibliothèque musicale locale (pas de streaming Qobuz/Tidal pour l'instant)
- **Un ordi pour faire tourner le serveur** — Windows, Linux, ou un Raspberry Pi

### Cartes NFC

N'importe quoi qui est NFC/RFID :
- Cartes MIFARE
- Badges d'accès
- Cartes de transport
- Stickers NFC
- Vieilles cartes bancaires

## Installation

### Sur Windows

1. **Installer Python 3.10+** depuis [python.org](https://python.org)

2. **Cloner le projet**
```bash
git clone https://github.com/CVerde/nfc-roon-controller.git
cd nfc-roon-controller
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer**
```bash
python serveur.py
```

Dans un autre terminal :
```bash
python nfc_reader.py
```

5. Ouvrir http://localhost:5000 dans un navigateur

### Sur Raspberry Pi

1. **Installer le système**

Raspberry Pi OS Lite suffit. Après le premier boot :

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git pcscd pcsc-tools
```

2. **Cloner et installer**
```bash
git clone https://github.com/CVerde/nfc-roon-controller.git
cd nfc-roon-controller
pip3 install -r requirements.txt --break-system-packages
```

3. **Tester que le lecteur NFC est détecté**
```bash
pcsc_scan
```
Tu devrais voir ton lecteur apparaître. Ctrl+C pour quitter.

4. **Configurer le démarrage automatique**
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nfc-roon-server nfc-roon-reader
sudo systemctl start nfc-roon-server nfc-roon-reader
```

5. Accéder à l'interface depuis un autre appareil : `http://IP_DU_PI:5000`

## Configuration de Roon

Au premier lancement, le système va essayer de se connecter à Roon. Il faut autoriser l'extension :

1. Ouvrir Roon sur ton ordi
2. Aller dans **Paramètres / Extensions**
3. Tu devrais voir "NFC Roon Controller" — cliquer sur **Activer**

Le token d'autorisation est sauvegardé automatiquement dans `roon_token.json`.

## Utilisation

### Programmer une carte

1. Ouvrir l'interface web (`http://localhost:5000` ou `http://IP_DU_PI:5000`)
2. Scanner une carte sur le lecteur — son identifiant apparaît
3. Chercher un album dans la bibliothèque
4. Sélectionner et sauvegarder

### Types de cartes

- **Album** — Lance un album spécifique
- **Genre** — Lance une lecture aléatoire d'un genre
- **Playlist** — Lance une playlist Roon
- **Pause** — Met en pause / reprend la lecture
- **Volume** — Règle le volume à un niveau précis
- **Shuffle** — Active/désactive la lecture aléatoire

### Choisir la zone

Par défaut, la musique se lance sur la première zone Roon disponible. On peut associer une carte à une zone précise dans l'interface.

### Écran d'affichage

Petit bonus.
Une page `/display` affiche la pochette et les infos de l'album en cours. Pratique sur une tablette ou un vieil écran dédié.
Cette page sera par la suite mise à jour pour être adaptée à un écran e-ink.

## Structure du projet

```
nfc-roon-controller/
├── serveur.py          # Serveur web Flask
├── nfc_reader.py       # Lecture des cartes NFC
├── roon_controller.py  # Communication avec Roon
├── config.py           # Configuration
├── utils.py            # Fonctions utilitaires
├── templates/
│   ├── admin.html      # Interface d'administration
│   └── display.html    # Affichage now playing
├── systemd/            # Services pour Raspberry Pi
└── scripts/            # Scripts de démarrage Windows
```

## Problèmes courants

### Le lecteur NFC n'est pas détecté

Sur Linux, vérifier que `pcscd` tourne :
```bash
sudo systemctl status pcscd
```

### Roon ne se connecte pas

- Vérifier que Roon est lancé sur le même réseau
- Supprimer `roon_token.json` et recommencer l'autorisation
- Parfois il faut juste relancer Roon...

### Les cartes ne sont pas lues

Certains badges ont une portée très courte. Essayer de poser la carte bien à plat sur le lecteur. Les cartes bancaires marchent bien en général. Les cartes de bibliothèque aussi. Les badges de porte également. Mais le mieux est d'acheter des cartes vierges en PVC ou des rouleaux de stickers.

## Roadmap

- Support des services de streaming (Qobuz, Tidal)
- Version avec HAT NFC pour Pi Zero (plus compact)
- Intégration dans un meuble. Plans pour l'impression 3D de pièces
- Écran e-ink pour un affichage permanent

## Licence

MIT

---
