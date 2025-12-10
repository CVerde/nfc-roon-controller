# NFC Roon Controller

Control your Roon music system with NFC cards. Tap a card, play an album.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

## Features

- 🎵 **Album playback** - Associate NFC cards with albums from your library
- 🎼 **Genre playback** - Shuffle music by genre
- 📋 **Playlist support** - Launch playlists with a tap
- ⏸️ **Playback controls** - Pause/play and volume cards
- 🌐 **Web interface** - Easy card programming via browser
- 🔄 **Auto-reconnect** - Robust connection handling with watchdog
- 🌍 **Multi-language** - English, French, Spanish, Chinese

## Hardware

### Required
- Roon Core (running on your network)
- NFC Reader (ACR122U USB recommended)
- NFC Cards (NTAG213/215/216 or Mifare Classic)

### Supported Platforms
- **Raspberry Pi** (recommended for standalone setup)
- **Windows** (with Android phone + Automate app for NFC reading)
- **Linux**

## Quick Start (Raspberry Pi)

### 1. Install dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv pcsc-tools pcscd libpcsclite-dev swig
sudo systemctl enable pcscd && sudo systemctl start pcscd
```

### 2. Clone and setup

```bash
git clone https://github.com/YOUR_USERNAME/nfc-roon-controller.git
cd nfc-roon-controller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. First run

```bash
python serveur.py
```

Open `http://YOUR_PI_IP:5001/admin` in your browser.

On first connection, authorize the extension in Roon: Settings → Extensions → Enable "NFC Roon Controller"

### 4. Test NFC reader

In a new terminal:

```bash
source venv/bin/activate
sudo /path/to/venv/bin/python nfc_reader.py
```

### 5. Install as service (auto-start on boot)

```bash
chmod +x scripts/install_pi.sh
sudo ./scripts/install_pi.sh
```

## Quick Start (Windows)

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Run server

```powershell
python serveur.py
```

### 3. NFC Reading options

**Option A: USB Reader**
```powershell
pip install pyscard
python nfc_reader.py
```

**Option B: Android phone with Automate app**
- Install [Automate](https://play.google.com/store/apps/details?id=com.llamalab.automate) on your phone
- Create a flow that sends NFC UID to: `http://YOUR_PC_IP:5001/badge?uid={uid}`

### 4. Auto-start (optional)

Right-click `scripts/install_autostart.ps1` → Run with PowerShell

## Configuration

### Default Zone

Edit `settings.json` (created on first run):

```json
{
  "default_zone": "Living Room",
  "language": "en"
}
```

### Files

| File | Description |
|------|-------------|
| `mapping.json` | Card-to-content associations (auto-created) |
| `settings.json` | User preferences (auto-created) |
| `stats.json` | Usage statistics (auto-created) |
| `roon_token.json` | Roon authentication token (auto-created) |

## Web Interface

### Admin Panel (`/admin`)

- Scan and program NFC cards
- Search albums in your library
- Select genres and playlists
- Create control cards (pause, volume)
- View usage statistics

### Display (`/display`)

- Now playing information
- Album artwork
- Progress bar
- Designed for a dedicated display

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/badge?uid=XXX` | GET/POST | Trigger card action |
| `/api/zones` | GET | List Roon zones |
| `/api/search?q=XXX` | GET | Search albums |
| `/api/genres` | GET | List genres |
| `/api/playlists` | GET | List playlists |
| `/api/cards` | GET | List programmed cards |
| `/api/now-playing` | GET | Current track info |
| `/api/stats` | GET | Usage statistics |

## Card Types

| Type | Description |
|------|-------------|
| Album | Play a specific album |
| Genre | Shuffle tracks from a genre |
| Playlist | Play a playlist |
| Pause | Toggle play/pause |
| Volume | Set volume to specific level |

## Troubleshooting

### NFC reader not detected

```bash
# Check USB connection
lsusb | grep -i acs

# Test reader
sudo pcsc_scan
```

### Roon connection issues

```bash
# Check logs
sudo journalctl -u nfc-roon-server -f

# Restart services
sudo systemctl restart nfc-roon-server nfc-roon-reader
```

### Permission denied on NFC

Run the reader with sudo or as root service (already configured in systemd).

## Project Structure

```
nfc-roon-controller/
├── serveur.py          # Flask web server
├── roon_controller.py  # Roon API integration
├── nfc_reader.py       # NFC card reader (Pi/Linux)
├── config.py           # Configuration
├── utils.py            # Utilities and helpers
├── templates/
│   ├── admin.html      # Admin interface
│   └── display.html    # Now playing display
├── systemd/            # Linux service files
└── scripts/            # Installation scripts
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- [python-roon-api](https://github.com/pavoni/pyroon) - Python Roon API
- [pyscard](https://github.com/LudovicRousseau/pyscard) - Python smart card library
