"""NFC Roon Controller - Utilities"""
import json
import os
import re
from datetime import datetime

# File paths
MAPPING_FILE = "mapping.json"
TOKEN_FILE = "roon_token.json"
STATS_FILE = "stats.json"


# === Mapping (card associations) ===

def load_mapping() -> dict:
    """Load card-to-content mapping from file"""
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_mapping(mapping: dict):
    """Save card-to-content mapping to file"""
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


# === Roon Token ===

def load_token() -> str | None:
    """Load Roon authentication token"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f).get("token")
        except:
            pass
    return None


def save_token(token: str):
    """Save Roon authentication token"""
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token}, f)


# === Statistics ===

def load_stats() -> dict:
    """Load usage statistics"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"cards": {}, "total_plays": 0, "first_use": None}


def save_stats(stats: dict):
    """Save usage statistics"""
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def record_play(uid: str, card_info: dict):
    """Record a card play in statistics"""
    stats = load_stats()
    
    now = datetime.now().isoformat()
    
    if not stats.get("first_use"):
        stats["first_use"] = now
    
    stats["total_plays"] = stats.get("total_plays", 0) + 1
    
    if uid not in stats.get("cards", {}):
        stats["cards"][uid] = {
            "plays": 0,
            "title": card_info.get("title", ""),
            "first_play": now
        }
    
    stats["cards"][uid]["plays"] += 1
    stats["cards"][uid]["last_play"] = now
    stats["cards"][uid]["title"] = card_info.get("title", stats["cards"][uid].get("title", ""))
    
    save_stats(stats)


def get_stats_summary() -> dict:
    """Get statistics summary for display"""
    stats = load_stats()
    
    # Sort cards by play count
    cards = stats.get("cards", {})
    top_cards = sorted(
        [{"uid": uid, **data} for uid, data in cards.items()],
        key=lambda x: x.get("plays", 0),
        reverse=True
    )[:10]
    
    return {
        "total_plays": stats.get("total_plays", 0),
        "unique_cards": len(cards),
        "first_use": stats.get("first_use"),
        "top_cards": top_cards
    }


# === Helpers ===

def clean_artist(artist: str) -> str:
    """Clean artist name from Roon format [[ID|Name]]"""
    if not artist:
        return ""
    return re.sub(r'\[\[[^\]]+\|([^\]]+)\]\]', r'\1', artist)
