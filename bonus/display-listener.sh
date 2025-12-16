#!/bin/bash

while true; do
  if [ -f "/tmp/display-now" ]; then
    if [ ! -f "/tmp/display-showing" ]; then
      # Premier scan - affiche
      rm /tmp/display-now
      killall -9 emulationstation-starter emulationstation 2>/dev/null
      sleep 2
      touch /tmp/display-showing
      
      # Boucle fbv tant que flag existe ET pas de nouveau scan
      while [ -f "/tmp/display-showing" ] && [ ! -f "/tmp/display-now" ]; do
        timeout 1 fbv -f -d /dev/fb0 /recalbox/share/nfc-roon-display/cache/artwork.bmp 2>/dev/null
        sleep 0.5
      done
      
      # Nettoie et relance ES
      rm /tmp/display-now /tmp/display-showing 2>/dev/null
      killall -9 fbv 2>/dev/null
      /etc/init.d/S31emulationstation start 2>/dev/null
      sleep 2
    fi
  fi
  
  sleep 1
done
