#!/bin/bash

while true; do
  if [ -f "/tmp/display-now" ]; then
    if [ ! -f "/tmp/display-showing" ]; then
      # Premier scan - affiche
      rm /tmp/display-now
      /etc/init.d/S31emulationstation stop 2>/dev/null
      sleep 2
      touch /tmp/display-showing
      
      # Boucle fbv tant que flag existe
      while [ -f "/tmp/display-showing" ]; do
        timeout 1 fbv -f -d /dev/fb0 /recalbox/share/nfc-roon-display/cache/artwork.bmp 2>/dev/null
        sleep 0.5
      done
    else
      # Deuxième scan - ferme
      rm /tmp/display-now 2>/dev/null
      rm /tmp/display-showing 2>/dev/null
      killall -9 fbv 2>/dev/null
      sleep 1
      /etc/init.d/S31emulationstation start 2>/dev/null
      sleep 2
    fi
  fi
  
  sleep 1
done
