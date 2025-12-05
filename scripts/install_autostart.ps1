# install_autostart.ps1
# Install NFC Roon Controller to start on Windows boot

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentPath = Split-Path -Parent $scriptPath
$vbsPath = Join-Path $scriptPath "start_hidden.vbs"
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "NFC-Roon-Controller.lnk"

# Create shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsPath`""
$Shortcut.WorkingDirectory = $parentPath
$Shortcut.Description = "NFC Roon Controller"
$Shortcut.Save()

Write-Host "Auto-start installed!" -ForegroundColor Green
Write-Host "Shortcut created: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall, delete the shortcut from:" -ForegroundColor Yellow
Write-Host $startupFolder -ForegroundColor Yellow
