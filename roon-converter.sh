#!/bin/bash

SERVER="http://192.168.1.60:5001/current-playing"
OUTPUT_FILE="/recalbox/share/dosbox-shared/artwork.bmp"
TEMP_FILE="/tmp/roon-temp.jpg"
last_url=""

while true; do
  URL=$(curl -s "$SERVER" 2>/dev/null | grep -o '"image_url":"[^"]*' | cut -d'"' -f4)
  
  if [ ! -z "$URL" ] && [ "$URL" != "$last_url" ]; then
    wget -q -O "$TEMP_FILE" "$URL" 2>/dev/null
    if [ -f "$TEMP_FILE" ] && [ -s "$TEMP_FILE" ]; then
      ffmpeg -y -i "$TEMP_FILE" -vf "scale=240:240, pad=320:240:(320-240)/2:(240-240)/2:black" "$OUTPUT_FILE" 2>/dev/null
      last_url="$URL"
    fi
  fi
  
  sleep 2
done
