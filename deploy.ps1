# NFC Roon Controller - Deploy Script
# Usage: .\deploy.ps1 "commit message"

param(
    [string]$Message = "Update"
)

$ProjectDir = "D:\MINSHARA\CODE\nfc-roon-controller"
$PiHost = "pi@192.168.1.60"
$PiDir = "~/nfc-roon"

Write-Host "=== NFC Roon Controller Deploy ===" -ForegroundColor Cyan

# 1. Push to GitHub
Write-Host "`n[1/3] Git push..." -ForegroundColor Yellow
Set-Location $ProjectDir
git add .
git commit -m $Message
git push

# 2. Copy files to Pi
Write-Host "`n[2/3] Copy to Pi..." -ForegroundColor Yellow
scp "$ProjectDir\serveur.py" "${PiHost}:${PiDir}/"
scp "$ProjectDir\roon_controller.py" "${PiHost}:${PiDir}/"
scp "$ProjectDir\config.py" "${PiHost}:${PiDir}/"
scp "$ProjectDir\utils.py" "${PiHost}:${PiDir}/"
scp "$ProjectDir\nfc_reader.py" "${PiHost}:${PiDir}/"
scp "$ProjectDir\templates\admin.html" "${PiHost}:${PiDir}/templates/"
scp "$ProjectDir\templates\display.html" "${PiHost}:${PiDir}/templates/"

# 3. Restart services on Pi
Write-Host "`n[3/3] Restart Pi services..." -ForegroundColor Yellow
ssh $PiHost "sudo systemctl restart nfc-roon-server && sudo systemctl restart nfc-roon-reader"

Write-Host "`n=== Done ===" -ForegroundColor Green
