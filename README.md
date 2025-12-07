# NFC Roon Controller

Contrôler sa musique avec des cartes NFC. Une carte est posée, l'album, la playlist, un genre definit... se lance.

![Demo](docs/demo.gif)

## Le projet ;

L'idée est de créer un système physique, tangible pour lancer de la musique depuis mon serveur Roon. Grace à un petit serveur python sur un Raspberry pi avec un lecteur RFID, j'ai créé ce petit projet qui permet de lancer la lecture d'albums spécifiques, de playlists ou même de genres. Certaines cartes spéciales permettent même de changer le volume, de mettre pause/play, d'activer le shuffle. Pour résumer, il s'agit de contrôler Roon avec un deck de cartes sans utiliser de téléphone ou d'ordinateur.

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
git clone https://github.com/ton-compte/nfc-roon-controller.git
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
git clone https://github.com/ton-compte/nfc-roon-controller.git
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

![Interface admin](docs/admin.png)

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

Petit bonus
Une page `/display` affiche la pochette et les infos de l'album en cours. Pratique sur une tablette ou un vieil écran dédié.
Cette page sera par la suite mise à jour pour $etre adaptée à un écran e-ink.

![Affichage](docs/display.png)

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

Certains badges ont une portée très courte. Essayer de poser la carte bien à plat sur le lecteur. Les cartes bancaires marchent bien en général. Les cartes de bibliothèque aussi. Les badges de porte également. Mais le mieux est d'acheter des cartes vierges en pvc ou des rouleaux de stickers.

## Roadmap

- Traduction du readme en anglais
- Support des services de streaming (Qobuz, Tidal)
- Version avec HAT NFC pour Pi Zero (plus compact)
- Intégration dans un meuble. Plans pour l'impression 3D de pièces et 
- Écran e-ink pour un affichage permanent

## Licence

MIT

---
