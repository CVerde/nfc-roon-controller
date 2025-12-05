"""NFC Roon Controller - Roon API Integration"""
from roonapi import RoonApi, RoonDiscovery
from contextlib import contextmanager
import threading
import time
from config import APP_INFO, SETTINGS
from utils import load_token, save_token

_lock = threading.Lock()


class RoonController:
    """Controller for Roon API interactions"""
    
    def __init__(self):
        self.api = None
        self._zone_cache = {}
        self._reconnect_thread = None
        self._should_run = True
        self._last_activity = time.time()

    def connect(self) -> bool:
        """Connect to Roon server"""
        try:
            servers = RoonDiscovery(None).all()
            if not servers:
                print("No Roon server found")
                return False

            token = load_token()
            self.api = RoonApi(APP_INFO, token, *servers[0])

            if self.api.token != token:
                save_token(self.api.token)
                print("Token saved")

            print(f"Roon connected: {servers[0][0]}:{servers[0][1]}")
            self._zone_cache.clear()
            self._last_activity = time.time()
            
            # Start watchdog thread
            self._start_watchdog()
            return True
        except Exception as e:
            print(f"Roon connection error: {e}")
            return False

    def _start_watchdog(self):
        """Start connection monitoring thread"""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        
        self._should_run = True
        self._reconnect_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._reconnect_thread.start()
        print("Watchdog started")

    def _watchdog_loop(self):
        """Monitor connection every 30 seconds"""
        while self._should_run:
            time.sleep(30)
            try:
                if not self._is_connected():
                    print("Roon connection lost, reconnecting...")
                    self._reconnect()
            except Exception as e:
                print(f"Watchdog error: {e}")

    def _is_connected(self) -> bool:
        """Check if Roon connection is active"""
        if not self.api:
            return False
        try:
            _ = self.api.zones
            return True
        except:
            return False

    def _reconnect(self):
        """Attempt to reconnect"""
        for attempt in range(3):
            print(f"Reconnection attempt {attempt + 1}/3...")
            try:
                if self.connect():
                    print("Reconnection successful")
                    return True
            except Exception as e:
                print(f"Failed: {e}")
            time.sleep(5)
        print("Reconnection failed after 3 attempts")
        return False

    def _ensure_connected(self) -> bool:
        """Ensure connection is active before operation"""
        if self._is_connected():
            self._last_activity = time.time()
            return True
        return self._reconnect()

    def _get_zone_id(self, ref=None) -> str | None:
        """Resolve zone_id from name or ID"""
        if not self._ensure_connected():
            return None

        # Direct ID
        if ref and ref in self.api.zones:
            return ref

        # Search by name (with cache)
        if ref:
            if ref in self._zone_cache:
                cached = self._zone_cache[ref]
                if cached in self.api.zones:
                    return cached
                del self._zone_cache[ref]
            
            for zid, z in self.api.zones.items():
                if z.get("display_name") == ref:
                    self._zone_cache[ref] = zid
                    return zid

        # Default zone from settings
        default_zone = SETTINGS.get("default_zone", "")
        if default_zone:
            for zid, z in self.api.zones.items():
                if z.get("display_name") == default_zone:
                    return zid

        # First available
        return next(iter(self.api.zones), None)

    def get_zone_name(self, zid: str) -> str | None:
        """Get zone name from ID"""
        try:
            if self._ensure_connected() and zid and zid in self.api.zones:
                return self.api.zones[zid].get("display_name")
        except:
            pass
        return None

    def get_zones(self) -> list:
        """List all zones"""
        if not self._ensure_connected():
            return []
        try:
            return [{"zone_id": z, "name": d.get("display_name", "?"), "state": d.get("state", "?")}
                    for z, d in self.api.zones.items()]
        except Exception as e:
            print(f"Error getting zones: {e}")
            return []

    # === Playback ===

    def play_content(self, content_type: str, data: dict, zone_id=None) -> bool:
        """Main entry point for playback"""
        if not self._ensure_connected():
            print("Roon not connected")
            return False

        zid = self._get_zone_id(zone_id)
        if not zid:
            print("Zone not found")
            return False

        print(f"Zone: {self.get_zone_name(zid)}")

        try:
            handlers = {
                "album": lambda: self._play_album(data.get("title"), data.get("artist"), zid),
                "genre": lambda: self._play_genre(data.get("genre"), data.get("subgenre"), zid),
                "playlist": lambda: self._play_playlist(data.get("playlist"), zid),
            }
            return handlers.get(content_type, lambda: False)()
        except Exception as e:
            print(f"Playback error: {e}")
            return False

    def _play_album(self, title, artist, zid) -> bool:
        """Play album with fallback paths"""
        paths = [["Library", "Albums", title], ["Library", "Artists", artist, title]]
        for path in paths:
            try:
                self.api.play_media(zid, path)
                print(f"Playing: {title}")
                return True
            except:
                continue
        print(f"Failed to play: {artist} - {title}")
        return False

    def _play_genre(self, genre, subgenre, zid) -> bool:
        """Play genre"""
        try:
            path = ["Genres", genre] + ([subgenre] if subgenre else [])
            self.api.play_media(zid, path)
            print(f"Playing: {' > '.join(path[1:])}")
            return True
        except Exception as e:
            print(f"Genre playback failed: {e}")
            return False

    def _play_playlist(self, playlist, zid) -> bool:
        """Play playlist"""
        try:
            result = self.api.play_media(zid, ["Playlists", playlist])
            if result is False or (isinstance(result, dict) and result.get("action") == "message"):
                print(f"Smart playlist not supported: {playlist}")
                return False
            print(f"Playing: {playlist}")
            return True
        except:
            print(f"Smart playlist not supported: {playlist}")
            return False

    # === Controls ===

    def control_playback(self, action: str, value=None, zone_id=None) -> bool:
        """Control playback (pause/volume)"""
        if not self._ensure_connected():
            print("Roon not connected")
            return False

        zid = self._get_zone_id(zone_id)
        if not zid:
            print("Zone not found")
            return False

        try:
            zone = self.api.zones.get(zid)
            print(f"Zone: {zone.get('display_name', zid)}")

            if action == "pause":
                self.api.playback_control(zid, "playpause")
                print("Pause/Play OK")
                return True

            if action == "volume":
                outputs = zone.get("outputs", [])
                if not outputs:
                    print("No output found")
                    return False

                output_id = outputs[0].get("output_id")
                vol = int(value) if value is not None else 50
                print(f"Volume: output={output_id}, value={vol}")
                
                self.api.set_volume_percent(output_id, vol)
                print(f"Volume set: {vol}")
                return True

        except Exception as e:
            print(f"Control error: {e}")
        return False

    # === Browse with context manager ===

    @contextmanager
    def _browse(self, target: str):
        """Context manager for browse navigation"""
        with _lock:
            try:
                self.api.browse_browse({"hierarchy": "browse", "pop_all": True})
                root = self.api.browse_load({"hierarchy": "browse", "offset": 0, "count": 50})

                key = next((i["item_key"] for i in root.get("items", []) if i.get("title") == target), None)
                if key:
                    self.api.browse_browse({"hierarchy": "browse", "item_key": key})
                    yield self.api.browse_load({"hierarchy": "browse", "offset": 0, "count": 200})
                else:
                    yield None
            except Exception as e:
                print(f"Browse error: {e}")
                yield None

    def get_genres(self) -> list:
        """List genres"""
        if not self._ensure_connected():
            return []
        with self._browse("Genres") as items:
            if not items:
                return []
            result = [{"name": i["title"]} for i in items.get("items", []) if i.get("title")]
            print(f"{len(result)} genres found")
            return result

    def get_subgenres(self, genre: str) -> list:
        """List subgenres for a genre"""
        if not self._ensure_connected():
            return []
        with self._browse("Genres") as items:
            if not items:
                return []
            key = next((i["item_key"] for i in items.get("items", []) if i.get("title") == genre), None)
            if not key:
                return []
            self.api.browse_browse({"hierarchy": "browse", "item_key": key})
            sub = self.api.browse_load({"hierarchy": "browse", "offset": 0, "count": 200})
            result = [{"name": i["title"]} for i in sub.get("items", []) if i.get("title")]
            print(f"{len(result)} subgenres for {genre}")
            return result

    def get_playlists(self) -> list:
        """List playlists"""
        if not self._ensure_connected():
            return []
        with self._browse("Playlists") as items:
            if not items:
                return []
            result = [{"name": i["title"]} for i in items.get("items", []) if i.get("title")]
            print(f"{len(result)} playlists found")
            return result

    def search(self, query: str) -> list:
        """Search albums"""
        if not self._ensure_connected() or len(query) < 2:
            return []

        with _lock:
            try:
                self.api.browse_browse({"hierarchy": "search", "input": query, "pop_all": True})
                cats = self.api.browse_load({"hierarchy": "search", "offset": 0, "set_display_offset": 0})

                key = next((i["item_key"] for i in cats.get("items", []) if i.get("title") == "Albums"), None)
                if not key:
                    return []

                self.api.browse_browse({"hierarchy": "search", "item_key": key})
                albums = self.api.browse_load({"hierarchy": "search", "offset": 0, "set_display_offset": 0, "count": 20})

                results = [
                    {"title": i.get("title", ""), "subtitle": i.get("subtitle", ""),
                     "hint": i.get("hint", ""), "image_key": i.get("image_key", "")}
                    for i in albums.get("items", [])[:15]
                    if not any(s in i.get("hint", "").lower() for s in ["qobuz", "tidal", "streaming"])
                ]
                print(f"Search '{query}': {len(results)} results")
                return results
            except Exception as e:
                print(f"Search error: {e}")
                return []

    def get_image_url(self, key: str) -> str | None:
        """Get image URL from key"""
        if not self._ensure_connected() or not key:
            return None
        try:
            return self.api.get_image(key)
        except:
            return None

    def get_now_playing(self, zone_id=None) -> dict | None:
        """Get current track information"""
        if not self._ensure_connected():
            return None

        try:
            zid = self._get_zone_id(zone_id)
            if not zid or zid not in self.api.zones:
                return None

            zone = self.api.zones[zid]
            now = zone.get("now_playing")
            if not now:
                return None

            return {
                "title": now.get("three_line", {}).get("line1", ""),
                "artist": now.get("three_line", {}).get("line2", ""),
                "album": now.get("three_line", {}).get("line3", ""),
                "image_key": now.get("image_key", ""),
                "length": now.get("length", 0),
                "seek_position": now.get("seek_position"),
                "state": zone.get("state", "stopped"),
                "zone_name": zone.get("display_name", "")
            }
        except Exception as e:
            print(f"Error getting now playing: {e}")
            return None
