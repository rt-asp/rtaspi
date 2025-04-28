#!/bin/bash
# Instalacja modeli STT i TTS dla rtaspi

set -e  # Zatrzymanie przy błędzie

echo "===== Instalacja modeli STT i TTS dla rtaspi ====="

# Katalog modeli
MODELS_DIR="$HOME/.rtaspi/models"
mkdir -p $MODELS_DIR/{stt,tts}

# Pobieranie i kompilacja Whisper.cpp
echo "[1/3] Instalacja Whisper.cpp..."
cd /tmp
if [ ! -d "whisper.cpp" ]; then
  git clone https://github.com/ggerganov/whisper.cpp.git
  cd whisper.cpp
else
  cd whisper.cpp
  git pull
fi

# Kompilacja
make

# Kopiowanie plików binarnych
echo "Kopiowanie plików binarnych whisper.cpp..."
cp main $MODELS_DIR/stt/
cp -r models $MODELS_DIR/stt/

# Pobieranie małego modelu
echo "Pobieranie modelu Whisper..."
cd $MODELS_DIR/stt/models
bash download-ggml-model.sh tiny

# Instalacja Piper TTS
echo "[2/3] Instalacja Piper TTS..."
cd /tmp
if [ ! -d "piper" ]; then
  git clone https://github.com/rhasspy/piper.git
  cd piper
else
  cd piper
  git pull
fi

# Instalacja Piper
pip3 install -e .

# Pobieranie modelu głosu dla Piper
echo "[3/3] Pobieranie modelu głosu dla Piper..."
mkdir -p $HOME/.local/share/piper/voices/
cd $HOME/.local/share/piper/voices/
wget https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-pl-krzysztof-low.tar.gz -O - | tar -xz

echo "===== Instalacja modeli zakończona! ====="
echo "Modele STT zainstalowane w: $MODELS_DIR/stt"
echo "Modele TTS zainstalowane w: $HOME/.local/share/piper/voices/"