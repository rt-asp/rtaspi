#!/bin/bash
# Konfiguracja usługi systemd dla rtaspi

set -e  # Zatrzymanie przy błędzie

echo "===== Konfiguracja usługi systemd dla rtaspi ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Ścieżka do zainstalowanego pakietu
rtaspi_PATH=$(pip3 show rtaspi | grep "Location" | awk '{print $2}')
if [ -z "$rtaspi_PATH" ]; then
  echo "Błąd: Nie znaleziono pakietu rtaspi. Czy został zainstalowany?"
  exit 1
fi

# Utworzenie usługi systemd
echo "Tworzenie usługi systemd..."
cat > /etc/systemd/system/rtaspi.service << EOF
[Unit]
Description=rtaspi - Bezpieczny interfejs głosowy AI dla dzieci
After=network.target

[Service]
ExecStart=/usr/bin/python3 -m rtaspi
WorkingDirectory=/home/$SUDO_USER
StandardOutput=journal
StandardError=journal
Restart=always
User=$SUDO_USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Aktywacja usługi
echo "Aktywacja usługi..."
systemctl daemon-reload
systemctl enable rtaspi.service

echo "===== Konfiguracja usługi zakończona! ====="
echo "Aby uruchomić usługę: sudo systemctl start rtaspi"
echo "Aby sprawdzić status: sudo systemctl status rtaspi"
echo "Aby zatrzymać usługę: sudo systemctl stop rtaspi"