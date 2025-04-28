#!/bin/bash
# Optymalizacja Raspberry Pi dla rtaspi

set -e  # Zatrzymanie przy błędzie

echo "===== Optymalizacja Raspberry Pi dla rtaspi ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Wyłączenie zbędnych usług
echo "[1/5] Wyłączanie zbędnych usług..."
systemctl disable bluetooth.service
systemctl disable avahi-daemon.service
systemctl disable triggerhappy.service
systemctl stop bluetooth.service
systemctl stop avahi-daemon.service
systemctl stop triggerhappy.service
echo "Usługi wyłączone."

# Optymalizacja config.txt
echo "[2/5] Optymalizacja /boot/config.txt..."
if ! grep -q "# rtaspi optimizations" /boot/config.txt; then
  echo "" >> /boot/config.txt
  echo "# rtaspi optimizations" >> /boot/config.txt
  echo "gpu_mem=16" >> /boot/config.txt
  echo "dtoverlay=disable-bt" >> /boot/config.txt
  echo "disable_splash=1" >> /boot/config.txt
  echo "force_turbo=1" >> /boot/config.txt
  echo "Dodano optymalizacje do /boot/config.txt"
else
  echo "Optymalizacje już istnieją w /boot/config.txt"
fi

# Optymalizacja zarządzania pamięcią
echo "[3/5] Optymalizacja zarządzania pamięcią..."
if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
  echo "" >> /etc/sysctl.conf
  echo "# rtaspi optimizations" >> /etc/sysctl.conf
  echo "vm.swappiness=10" >> /etc/sysctl.conf
  echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
  echo "Dodano optymalizacje pamięci."
else
  echo "Optymalizacje pamięci już istnieją."
fi

# Konfiguracja zasilania
echo "[4/5] Konfiguracja zarządzania energią..."
if which powertop >/dev/null; then
  powertop --auto-tune
  echo "Zastosowano optymalizacje powertop."
else
  echo "Powertop nie jest zainstalowany. Pomijanie."
fi

# Ustawienie częstotliwości CPU
echo "[5/5] Konfiguracja częstotliwości CPU..."
if which cpufreq-set >/dev/null; then
  cpufreq-set -g ondemand
  echo "Ustawiono tryb ondemand dla CPU."
else
  echo "cpufreq-set nie jest zainstalowany. Pomijanie."
fi

echo "===== Optymalizacja zakończona! ====="
echo "Proszę zrestartować urządzenie, aby zastosować wszystkie zmiany."