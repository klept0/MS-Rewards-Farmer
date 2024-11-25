#!/bin/bash

bash makeConfiguration.sh

rm -f /tmp/.X0-lock

# Run Xvfb on dispaly 0.
Xvfb :0 -screen 0 1920x1080x24 &

# Run fluxbox windows manager on display 0.
fluxbox -display :0 &

# Run x11vnc on display 0
x11vnc -display :0 -forever -usepw &

# Add delay
sleep 10

# Default "US"
GEOLOCATION=${GEOLOCATION:-US}

# Language default "en"
LANG=${lang:-en}

# starts script
python3 main.py -v -l "$LANG" -g "$GEOLOCATION"