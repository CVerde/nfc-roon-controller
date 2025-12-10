#!/bin/bash

if [ "$1" = "start" ]; then
  nohup bash /recalbox/share/nfc-roon-display/roon-converter.sh > /tmp/roon-converter.log 2>&1 &
  nohup bash /recalbox/share/nfc-roon-display/display-listener.sh > /tmp/display-listener.log 2>&1 &
fi
