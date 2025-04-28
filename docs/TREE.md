
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
