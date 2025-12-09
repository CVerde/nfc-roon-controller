"""NFC Roon Controller - Flask Web Server"""
from flask import Flask, request, render_template, jsonify, redirect
from dataclasses import dataclass, field
import time
import socket
import logging
from roon_controller import RoonController
from utils import load_mapping, save_mapping, clean_artist, record_play, get_stats_summary
from config import SERVER_PORT, SCAN_TIMEOUT, SETTINGS, save_settings, load_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@dataclass
class State:
    """Centralized application state"""
    mapping: dict = field(default_factory=load_mapping)
    roon: RoonController = field(default_factory=RoonController)
    last_uid: str = None
    last_time: float = 0
    playing: dict = None

    def scan(self, uid: str):
        self.last_uid, self.last_time = uid, time.time()

    def valid_scan(self) -> bool:
        return self.last_uid and (time.time() - self.last_time) < SCAN_TIMEOUT


state = State()


def init_roon():
    """Initialize Roon connection with retry"""
    for attempt in range(3):
        logger.info(f"Connecting to Roon (attempt {attempt + 1}/3)...")
        if state.roon.connect():
            logger.info("Roon connected")
            return True
        time.sleep(2)
    logger.warning("Could not connect to Roon at startup")
    return False


init_roon()


def get_uid():
    """Extract UID from request"""
    uid = (request.form.get("uid") or
           request.args.get("uid") or
           (request.get_json(silent=True) or {}).get("uid"))
    if not uid and "uid=" in (raw := request.get_data(as_text=True)):
        uid = raw.split("uid=")[1].split("&")[0]
    return uid.upper() if uid else None


# === Main Routes ===

@app.route("/badge", methods=["POST", "GET"])
def badge():
    """Handle NFC badge scan"""
    try:
        uid = get_uid()
        if not uid:
            return jsonify({"status": "error", "message": "no uid"}), 400

        state.scan(uid)
        logger.info(f"Badge scanned: {uid}")

        if uid not in state.mapping:
            logger.info("Card not programmed")
            return jsonify({"status": "unknown", "uid": uid})

        card = state.mapping[uid]
        action = card.get("action", "play")
        zone_id = card.get("zone_id")

        # Control actions
        if action == "pause":
            logger.info("Action: Pause/Play")
            ok = state.roon.control_playback("pause", zone_id=zone_id)
            return jsonify({"status": "control" if ok else "error", "action": "pause"})

        if action == "volume":
            vol = card.get("volume", 50)
            logger.info(f"Action: Volume {vol}")
            ok = state.roon.control_playback("volume", vol, zone_id=zone_id)
            return jsonify({"status": "control" if ok else "error", "action": "volume", "level": vol})

        if action == "shuffle":
            logger.info("Action: Shuffle")
            ok = state.roon.control_playback("shuffle", zone_id=zone_id)
            return jsonify({"status": "control" if ok else "error", "action": "shuffle"})

        # Content playback
        ctype = card.get("content_type", "album")
        data = {
            "album": {"title": card.get("title"), "artist": card.get("artist")},
            "genre": {"genre": card.get("genre"), "subgenre": card.get("subgenre")},
            "playlist": {"playlist": card.get("playlist")},
        }.get(ctype, {})

        logger.info(f"{ctype}: {data}")
        ok = state.roon.play_content(ctype, data, zone_id=zone_id)
        if ok:
            state.playing = card
            record_play(uid, card)
        return jsonify({"status": "playing" if ok else "error"})

    except Exception as e:
        logger.error(f"Badge error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/display")
def display():
    return render_template("display.html")


# === API ===

@app.route("/api/zones")
def api_zones():
    return jsonify(state.roon.get_zones())


@app.route("/api/genres")
def api_genres():
    return jsonify(state.roon.get_genres())


@app.route("/api/subgenres/<genre>")
def api_subgenres(genre):
    return jsonify(state.roon.get_subgenres(genre))


@app.route("/api/playlists")
def api_playlists():
    return jsonify(state.roon.get_playlists())


@app.route("/api/search")
def api_search():
    return jsonify(state.roon.search(request.args.get("q", "")))


@app.route("/api/image/<key>")
def api_image(key):
    url = state.roon.get_image_url(key)
    return redirect(url) if url else ("", 404)


@app.route("/api/last-scan")
def api_last_scan():
    return jsonify({"uid": state.last_uid if state.valid_scan() else None})


@app.route("/api/now-playing")
def api_now_playing():
    # Info from Roon (current track)
    roon_info = state.roon.get_now_playing()
    # Info from our state (scanned card)
    card_info = state.playing
    
    return jsonify({
        "card": card_info,
        "track": roon_info
    })


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats_summary())


@app.route("/api/settings")
def api_settings_get():
    return jsonify(load_settings())


@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    data = request.json
    settings = load_settings()
    settings.update(data)
    save_settings(settings)
    # Reload settings
    global SETTINGS
    SETTINGS = load_settings()
    return jsonify({"status": "success"})


# === Card Management ===

@app.route("/api/cards")
def api_cards():
    """List all programmed cards"""
    cards = []
    for uid, data in state.mapping.items():
        card = {"uid": uid, **data}
        if data.get("zone_id"):
            card["zone_name"] = state.roon.get_zone_name(data["zone_id"])
        cards.append(card)
    return jsonify(cards)


@app.route("/api/cards", methods=["POST"])
def api_cards_post():
    """Add or update a card"""
    data = request.json
    uid = data.get("uid", "").upper()
    if not uid:
        return jsonify({"status": "error", "message": "No UID"}), 400

    action = data.get("action", "play")
    
    if action == "play":
        ctype = data.get("content_type", "album")
        
        if ctype == "album":
            # Parse year from hint (format: "2023" or "2023 • Jazz")
            hint = data.get("hint", "")
            year = ""
            if hint:
                parts = hint.split("•")
                if parts and parts[0].strip().isdigit():
                    year = parts[0].strip()
            
            card = {
                "action": "play",
                "content_type": "album",
                "title": data.get("title"),
                "artist": clean_artist(data.get("artist", "")),
                "image_key": data.get("image_key", ""),
                "year": year,
                "hint": hint
            }
        elif ctype == "genre":
            card = {
                "action": "play",
                "content_type": "genre",
                "genre": data.get("genre"),
                "subgenre": data.get("subgenre"),
                "title": data.get("subgenre") or data.get("genre"),
                "artist": "Genre"
            }
        elif ctype == "playlist":
            card = {
                "action": "play",
                "content_type": "playlist",
                "playlist": data.get("playlist"),
                "title": data.get("playlist"),
                "artist": "Playlist"
            }
        else:
            return jsonify({"status": "error", "message": "Invalid type"}), 400
            
    elif action == "pause":
        card = {"action": "pause", "title": "Pause/Play", "artist": "Control"}
        
    elif action == "volume":
        card = {
            "action": "volume",
            "volume": data.get("volume", 50),
            "title": f"Volume {data.get('volume', 50)}%",
            "artist": "Control"
        }
    elif action == "shuffle":
        card = {"action": "shuffle", "title": "Shuffle", "artist": "Control"}
    else:
        return jsonify({"status": "error", "message": "Invalid action"}), 400

    # Add zone if specified
    if data.get("zone_id"):
        card["zone_id"] = data["zone_id"]

    state.mapping[uid] = card
    save_mapping(state.mapping)
    logger.info(f"Card saved: {uid} -> {card.get('title')}")
    return jsonify({"status": "success"})


@app.route("/api/cards/<uid>", methods=["DELETE"])
def api_cards_delete(uid):
    """Delete a card"""
    uid = uid.upper()
    if uid not in state.mapping:
        return jsonify({"status": "error", "message": "Not found"}), 404
    del state.mapping[uid]
    save_mapping(state.mapping)
    return jsonify({"status": "success"})


@app.route("/api/test-play", methods=["POST"])
def api_test_play():
    """Test play a card"""
    uid = request.json.get("uid", "").upper()
    if uid not in state.mapping:
        return jsonify({"status": "error", "message": "Not found"}), 404

    card = state.mapping[uid]
    action = card.get("action", "play")
    zone_id = card.get("zone_id")

    if action == "pause":
        ok = state.roon.control_playback("pause", zone_id=zone_id)
    elif action == "volume":
        ok = state.roon.control_playback("volume", card.get("volume", 50), zone_id=zone_id)
    else:
        ctype = card.get("content_type", "album")
        data = {
            "album": {"title": card.get("title"), "artist": card.get("artist")},
            "genre": {"genre": card.get("genre"), "subgenre": card.get("subgenre")},
            "playlist": {"playlist": card.get("playlist")},
        }.get(ctype, {})
        ok = state.roon.play_content(ctype, data, zone_id=zone_id)

    return jsonify({"status": "success" if ok else "error"})


# === PDF Export ===

@app.route("/api/export-pdf")
def api_export_pdf():
    """Generate PDF with album covers (4.5cm each)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from io import BytesIO
    from flask import send_file
    import urllib.request

    # Settings
    COVER_SIZE = 4.5 * cm
    MARGIN = 1 * cm
    SPACING = 0.3 * cm

    # Get cards with images
    cards = []
    for uid, data in state.mapping.items():
        if data.get("image_key") and data.get("action") == "play":
            cards.append(data)

    if not cards:
        return jsonify({"status": "error", "message": "No cards with covers"}), 400

    # Create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Calculate grid
    cols = int((width - 2 * MARGIN + SPACING) / (COVER_SIZE + SPACING))
    rows = int((height - 2 * MARGIN + SPACING) / (COVER_SIZE + SPACING))

    x_start = MARGIN
    y_start = height - MARGIN - COVER_SIZE

    col = 0
    row = 0

    for card in cards:
        # Position
        x = x_start + col * (COVER_SIZE + SPACING)
        y = y_start - row * (COVER_SIZE + SPACING)

        # Get image
        try:
            img_url = state.roon.get_image_url(card.get("image_key"))
            if img_url:
                img_data = urllib.request.urlopen(img_url, timeout=10).read()
                img_buffer = BytesIO(img_data)
                img = ImageReader(img_buffer)
                c.drawImage(img, x, y, width=COVER_SIZE, height=COVER_SIZE)
                # Draw thin black border for cutting guide
                c.setStrokeColorRGB(0, 0, 0)
                c.setLineWidth(0.5)
                c.rect(x, y, COVER_SIZE, COVER_SIZE, stroke=1, fill=0)
        except Exception as e:
            # Draw placeholder with title
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.rect(x, y, COVER_SIZE, COVER_SIZE)
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            title = card.get("title", "?")[:25]
            c.drawString(x + 5, y + COVER_SIZE/2, title)

        # Next position
        col += 1
        if col >= cols:
            col = 0
            row += 1
            if row >= rows:
                c.showPage()
                row = 0

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        download_name='nfc-covers.pdf',
        as_attachment=True
    )


@app.route('/current', methods=['GET'])
def get_current():
    """Endpoint minimaliste pour Dreamcast"""
    if not current_playing:
        return jsonify({"playing": False})

    image_url = ""
    if current_playing.get('image_key'):
        image_url = f"http://192.168.1.153:5000/api/image/{current_playing['image_key']}"

    return jsonify({
        "playing": True,
        "title": current_playing.get('title', 'Unknown'),
        "artist": current_playing.get('artist', 'Unknown'),
        "image_url": image_url
    })


# === Error Handlers ===

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler"""
    logger.error(f"Unhandled error: {e}")
    return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Not found"}), 404


# === Main ===

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    logger.info("=" * 50)
    logger.info("NFC Roon Controller v2.1")
    logger.info(f"http://{ip}:{SERVER_PORT}/admin")
    logger.info("=" * 50)
    
    # Reduce werkzeug logging verbosity
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False, threaded=True)
