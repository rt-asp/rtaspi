#!/bin/bash
# Konfiguracja sprzętu dla rtaspi

set -e  # Zatrzymanie przy błędzie

echo "===== Konfiguracja sprzętu dla rtaspi ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Włączenie interfejsów
echo "[1/3] Włączanie interfejsów..."
raspi-config nonint do_spi 0  # Włącz SPI
raspi-config nonint do_i2c 0  # Włącz I2C

# Konfiguracja GPIO
echo "[2/3] Konfiguracja pinów GPIO..."
# Ta część może się różnić w zależności od podłączonego sprzętu
# Tutaj tylko przykładowa konfiguracja

# Konfiguracja urządzenia audio
echo "[3/3] Konfiguracja urządzenia audio..."
# Wykrywanie podłączonego urządzenia ReSpeaker
if aplay -l | grep -q "seeed"; then
  echo "Wykryto urządzenie ReSpeaker."
  # Konfiguracja dla ReSpeaker
  cat > /etc/asound.conf << EOF
pcm.!default {
  type asym
  capture.pcm "mic"
  playback.pcm "speaker"
}

pcm.mic {
  type plug
  slave {
    pcm "hw:seeed2micvoicec"
    channels 1
    format S16_LE
    rate 16000
  }
}

pcm.speaker {
  type plug
  slave {
    pcm "hw:seeed2micvoicec"
    channels 1
    format S16_LE
    rate 16000
  }
}
EOF
  echo "Skonfigurowano ALSA dla ReSpeaker."
else
  echo "Nie wykryto urządzenia ReSpeaker. Używanie domyślnej konfiguracji audio."
fi

echo "===== Konfiguracja sprzętu zakończona! ====="
echo "Proszę zrestartować urządzenie, aby zastosować wszystkie zmiany."