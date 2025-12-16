# NFC Roon Display - Installation Recalbox

## Fichiers à copier sur Recalbox

### 1. Créer le dossier
```bash
ssh root@192.168.1.44
mkdir -p /recalbox/share/nfc-roon-display/cache
```

### 2. Copier les scripts
Depuis Windows :
```powershell
scp display-listener.sh root@192.168.1.44:/recalbox/share/nfc-roon-display/
scp roon-converter.sh root@192.168.1.44:/recalbox/share/nfc-roon-display/
scp custom.sh root@192.168.1.44:/recalbox/share/system/
```

### 3. Rendre exécutables
```bash
ssh root@192.168.1.44
chmod +x /recalbox/share/nfc-roon-display/*.sh
chmod +x /recalbox/share/system/custom.sh
```

### 4. Configurer SSH sans password (Pi4 → Recalbox)
Sur Pi4 :
```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@192.168.1.44
```

### 5. Redémarrer
```bash
reboot
```

## Vérification
Après reboot, vérifier que les scripts tournent :
```bash
ssh root@192.168.1.44
ps aux | grep -E "(roon-converter|display-listener)"
```

## Utilisation
- Scanner carte Display (UID: 0416FC8A3E6180) → affiche artwork
- Changer d'album sur Roon → artwork se met à jour
- Rescanner carte Display → retour à Emulation Station

## Dépendances Recalbox
- fbv (déjà installé)
- ffmpeg (déjà installé)
- curl, wget (déjà installés)
