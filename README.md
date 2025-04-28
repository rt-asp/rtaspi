
# rtaspi - Real-Time Annotation and Stream Processing [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/README.md)

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
git clone https://github.com/twoja-organizacja/rtaspi.git
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

 [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/TREE.md)
## Struktura projektu

```
rtaspi/
├── core/                       # Komponenty podstawowe
│   ├── config.py               # Obsługa konfiguracji
│   ├── logging.py              # Konfiguracja logowania
│   ├── mcp.py                  # Broker komunikacji międzymodułowej
│   └── utils.py                # Narzędzia pomocnicze
├── device_managers/            # Zarządzanie urządzeniami
│   ├── base.py                 # Podstawowa klasa menedżera
│   ├── local_devices.py        # Menedżer lokalnych urządzeń
│   ├── network_devices.py      # Menedżer zdalnych urządzeń sieciowych
│   └── utils/
│       ├── device.py           # Klasy bazowe dla urządzeń
│       ├── discovery.py        # Wykrywanie urządzeń (ONVIF, UPnP, mDNS)
│       └── protocols.py        # Obsługa protokołów streamingu
├── streaming/                  # Obsługa streamingu
│   ├── rtsp.py                 # Obsługa protokołu RTSP
│   ├── rtmp.py                 # Obsługa protokołu RTMP
│   ├── webrtc.py               # Obsługa protokołu WebRTC
│   └── utils.py                # Narzędzia pomocnicze do streamingu
├── tests/                      # Testy jednostkowe
│   ├── test_local_devices.py   # Testy menedżera lokalnych urządzeń
│   ├── test_network_devices.py # Testy menedżera zdalnych urządzeń
│   ├── test_discovery.py       # Testy wykrywania urządzeń
│   └── test_streaming.py       # Testy streamingu
├── main.py                     # Główny plik uruchomieniowy
├── config.yaml                 # Plik konfiguracyjny
└── requirements.txt            # Zależności projektu
```

 [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/INSTALL.md)
## Uruchomienie

1. Uruchom główny skrypt:
```bash
python main.py
```

2. Opcjonalnie, możesz podać ścieżkę do pliku konfiguracyjnego:
```bash
python main.py -c /sciezka/do/config.yaml
```

## Protokół komunikacyjny MCP

System używa wewnętrznego protokołu komunikacyjnego MCP (Module Communication Protocol) do wymiany informacji między modułami. Protokół opiera się na wzorcu publikuj/subskrybuj (pub/sub), gdzie moduły mogą publikować wiadomości na określone tematy i subskrybować tematy, aby otrzymywać wiadomości.

### Przykładowe tematy MCP:

- `local_devices/devices` - Informacje o wykrytych lokalnych urządzeniach
- `local_devices/stream/started` - Informacja o uruchomieniu strumienia z lokalnego urządzenia
- `network_devices/devices` - Informacje o wykrytych urządzeniach sieciowych
- `command/local_devices/scan` - Komenda do skanowania lokalnych urządzeń
- `command/network_devices/add_device` - Komenda do dodania zdalnego urządzenia

## Używanie API

System udostępnia API do zarządzania urządzeniami i strumieniami. Poniżej znajdują się przykłady użycia API w kodzie Python:

```python
from core.mcp import MCPBroker, MCPClient

# Utwórz klienta MCP
broker = MCPBroker()
client = MCPClient(broker, client_id="my_client")

# Subskrybuj tematy
client.subscribe("local_devices/devices", handler=handle_devices)
client.subscribe("local_devices/stream/started", handler=handle_stream_started)

# Wysyłaj komendy
client.publish("command/local_devices/scan", {})

# Uruchom strumień z urządzenia
client.publish("command/local_devices/start_stream", {
    "device_id": "video:/dev/video0",
    "protocol": "rtsp"
})

# Dodaj zdalne urządzenie
client.publish("command/network_devices/add_device", {
    "name": "Kamera IP",
    "ip": "192.168.1.100",
    "port": 554,
    "username": "admin",
    "password": "admin",
    "type": "video",
    "protocol": "rtsp",
    "paths": ["cam/realmonitor"]
})
```

## Testy

Uruchomienie testów jednostkowych:
```bash
pytest -v tests/
```

## Licencja

Ten projekt jest udostępniany na licencji Apache 2. Zobacz plik LICENSE, aby uzyskać więcej informacji.

## Autorzy

- Zespół rtaspi

## Współpraca

Zachęcamy do współpracy przy rozwoju projektu. Zapraszamy do zgłaszania problemów (issues) i propozycji zmian (pull requests).

---
+ Modular Documentation made possible by the [FlatEdit](http://www.flatedit.com) project.
