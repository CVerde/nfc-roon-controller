#!/usr/bin/env python3
"""NFC Roon Controller - NFC Card Reader (ACR122U)"""
import time
import requests
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

# Configuration
SERVER_URL = "http://localhost:5001/badge"
POLL_INTERVAL = 0.3  # seconds between scans
DEBOUNCE_TIME = 2.0  # seconds before re-reading same card


class NFCReader:
    """NFC card reader using ACR122U"""
    
    def __init__(self):
        self.last_uid = None
        self.last_time = 0
        self.reader = None

    def connect(self):
        """Connect to NFC reader"""
        try:
            r = readers()
            if not r:
                print("[NFC] No reader found")
                return False
            self.reader = r[0]
            print(f"[NFC] Reader: {self.reader}")
            
            # Disable buzzer
            try:
                conn = self.reader.createConnection()
                conn.connect()
                conn.transmit([0xFF, 0x00, 0x52, 0x00, 0x00])
                conn.disconnect()
                print("[NFC] Buzzer disabled")
            except:
                pass
            
            return True
        except Exception as e:
            print(f"[NFC] Error: {e}")
            return False

    def read_uid(self):
        """Read UID from card"""
        try:
            connection = self.reader.createConnection()
            connection.connect()
            # GET UID command for ISO 14443-A cards
            data, sw1, sw2 = connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
            if sw1 == 0x90 and sw2 == 0x00:
                return toHexString(data).replace(" ", "")
        except (NoCardException, CardConnectionException):
            pass
        except:
            pass
        return None

    def should_process(self, uid):
        """Check if card should be processed (debounce)"""
        now = time.time()
        if uid == self.last_uid and (now - self.last_time) < DEBOUNCE_TIME:
            return False
        self.last_uid = uid
        self.last_time = now
        return True

    def send_to_server(self, uid):
        """Send UID to server"""
        try:
            response = requests.get(f"{SERVER_URL}?uid={uid}", timeout=5)
            data = response.json()
            status = data.get("status", "unknown")
            
            if status == "playing":
                print(f"[NFC] {uid} -> Playing")
            elif status == "control":
                print(f"[NFC] {uid} -> {data.get('action')}")
            elif status == "unknown":
                print(f"[NFC] {uid} -> Not programmed")
            else:
                print(f"[NFC] {uid} -> Error: {data.get('message', status)}")
                
        except requests.exceptions.ConnectionError:
            print("[NFC] Server unavailable")
        except Exception as e:
            print(f"[NFC] Error: {e}")

    def run(self):
        """Main loop"""
        print("[NFC] Starting...")
        
        while not self.connect():
            print("[NFC] Retrying in 5s...")
            time.sleep(5)
        
        print("[NFC] Waiting for cards...")
        
        while True:
            try:
                uid = self.read_uid()
                
                if uid and self.should_process(uid):
                    print(f"[NFC] Card detected: {uid}")
                    self.send_to_server(uid)
                elif not uid:
                    # Card removed, allow re-scan
                    if self.last_uid:
                        self.last_uid = None
                
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("[NFC] Stopped")
                break
            except Exception as e:
                print(f"[NFC] Error: {e}")
                time.sleep(1)


if __name__ == "__main__":
    NFCReader().run()
