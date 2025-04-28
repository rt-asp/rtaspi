# rtaspi - Real-Time Annotation and Stream Processing

rtaspi to system do wykrywania, zarządzania i streamowania z lokalnych oraz zdalnych urządzeń audio i wideo. Umożliwia łatwe udostępnianie strumieni z kamer i mikrofonów w różnych protokołach (RTSP, RTMP, WebRTC).

## Główne funkcje

- Automatyczne wykrywanie lokalnych urządzeń wideo (kamery) i audio (mikrofony)
- Wykrywanie zdalnych urządzeń sieciowych (kamery IP, mikrofony IP) poprzez protokoły ONVIF, UPnP i mDNS
- Streamowanie z urządzeń lokalnych poprzez RTSP, RTMP i WebRTC
- Proxy strumieni z urządzeń zdalnych
- Transkodowanie strumieni w czasie rzeczywistym
- Centralny system komunikacji między modułami (MCP - Module Communication Protocol)

## Wymagania systemowe

- Python 3.8 lub nowszy
- FFmpeg 4.0 lub nowszy
- GStreamer 1.14 lub nowszy (dla WebRTC)
- NGINX z modułem RTMP (dla RTMP)

### Zależności systemowe

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly nginx libnginx-mod-rtmp v4l-utils
```

#### macOS:
```bash
brew install ffmpeg gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly nginx
```

#### Windows:
Pobierz i zainstaluj:
- [FFmpeg](https://ffmpeg.org/download.html)
- [GStreamer](https://gstreamer.freedesktop.org/download/)
- [NGINX z modułem RTMP](https://github.com/illuspas/nginx-rtmp-win32)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/rt-asp/rtaspi.git
cd rtaspi
```

2. Utwórz i aktywuj wirtualne środowisko:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

## Konfiguracja

Konfiguracja systemu znajduje się w pliku `config.yaml`. Domyślna konfiguracja zostanie utworzona automatycznie przy pierwszym uruchomieniu, możesz ją później dostosować do swoich potrzeb.

Przykładowa konfiguracja:
```yaml
system:
  storage_path: 'storage'
  log_level: 'INFO'

local_devices:
  enable_video: true
  enable_audio: true
  auto_start: false
  scan_interval: 60
  rtsp_port_start: 8554
  rtmp_port_start: 1935
  webrtc_port_start: 8080

network_devices:
  enable: true
  scan_interval: 60
  discovery_enabled: true
  discovery_methods:
    - 'onvif'
    - 'upnp'
    - 'mdns'
  rtsp_port_start: 8654
  rtmp_port_start: 2935
  webrtc_port_start: 9080

streaming:
  rtsp:
    port_start: 8554
  rtmp:
    port_start: 1935
  webrtc:
    port_start: 8080
    stun_server: 'stun://stun.l.google.com:19302'
    turn_server: ''
    turn_username: ''
    turn_password: ''
```
