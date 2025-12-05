#!/bin/bash
# ===========================================
# NFC Roon Controller - Raspberry Pi Setup
# ===========================================

set -e

echo ""
echo "====================================="
echo "  NFC Roon Controller - Installation"
echo "====================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# 1. System update
echo -e "${YELLOW}[1/6] Updating system...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. Install NFC dependencies
echo -e "${YELLOW}[2/6] Installing NFC dependencies...${NC}"
sudo apt install -y python3-pip python3-venv pcsc-tools pcscd libpcsclite-dev swig

# 3. Enable PC/SC service
echo -e "${YELLOW}[3/6] Enabling PC/SC service...${NC}"
sudo systemctl enable pcscd
sudo systemctl start pcscd

# 4. Setup Python environment
echo -e "${YELLOW}[4/6] Setting up Python environment...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Update service files with correct path
echo -e "${YELLOW}[5/6] Configuring services...${NC}"
sed -i "s|/home/pi/nfc-roon-controller|$INSTALL_DIR|g" systemd/nfc-roon-server.service
sed -i "s|/home/pi/nfc-roon-controller|$INSTALL_DIR|g" systemd/nfc-roon-reader.service

# Install services
sudo cp systemd/nfc-roon-server.service /etc/systemd/system/
sudo cp systemd/nfc-roon-reader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nfc-roon-server
sudo systemctl enable nfc-roon-reader

# 6. Start services
echo -e "${YELLOW}[6/6] Starting services...${NC}"
sudo systemctl start nfc-roon-server
sleep 3
sudo systemctl start nfc-roon-reader

# Check NFC reader
echo ""
echo "Checking NFC reader..."
if lsusb | grep -qi "acs\|acr"; then
    echo -e "${GREEN}✓ NFC reader detected${NC}"
else
    echo -e "${YELLOW}⚠ NFC reader not detected - check USB connection${NC}"
fi

# Display result
IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}====================================="
echo "  INSTALLATION COMPLETE!"
echo "=====================================${NC}"
echo ""
echo "Admin interface: http://$IP:5001/admin"
echo ""
echo "Useful commands:"
echo "  sudo journalctl -u nfc-roon-server -f   (view server logs)"
echo "  sudo journalctl -u nfc-roon-reader -f   (view reader logs)"
echo "  sudo systemctl restart nfc-roon-server  (restart server)"
echo "  sudo systemctl restart nfc-roon-reader  (restart reader)"
echo ""
