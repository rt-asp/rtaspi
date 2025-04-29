# Zaktualizowana Lista Zadań (TODO)


## 2. System Konfiguracji
- [ ] Zaimplementować hierarchiczny system konfiguracji:
  - [ ] Domyślna konfiguracja w kodzie (`src/rtaspi/core/defaults.py`)
  - [ ] Globalna konfiguracja (`rtaspi.config.yaml`)
  - [ ] Konfiguracja użytkownika (`~/.config/rtaspi/config.yaml`)
  - [ ] Konfiguracja projektu (`.rtaspi/config.yaml`)
  - [ ] Obsługa zmiennych środowiskowych (`.env`)
- [ ] Utworzyć schematy danych dla walidacji konfiguracji:
  - [ ] Zdefiniować `schemas/device.py` dla urządzeń
  - [ ] Zdefiniować `schemas/stream.py` dla strumieni
  - [ ] Zdefiniować `schemas/pipeline.py` dla pipelinów przetwarzania
- [ ] Implementacja `ConfigManager` z metodami:
  - [ ] `get_config(section, key, default=None)`
  - [ ] `set_config(section, key, value, level='user')`
  - [ ] `load_config_file(path)`
  - [ ] `save_config_file(path, level='user')`

## 4. API Biblioteki
- [ ] Zaimplementować publiczne API biblioteki:
  - [ ] `api/devices.py` - fasada do zarządzania urządzeniami
  - [ ] `api/streams.py` - fasada do zarządzania strumieniami
  - [ ] `api/pipelines.py` - fasada do zarządzania pipelinami
  - [ ] `api/server.py` - fasada do zarządzania serwerem webowym
- [ ] Zapewnić spójność między API a CLI (używanie tych samych fasad)
- [ ] Dodać obszerne docstringi z przykładami użycia

## 5. Uproszczone API dla Juniorów
- [ ] Stworzyć moduł `quick/` z prostymi interfejsami:
  - [ ] `quick/camera.py` z funkcjami dla kamer
  - [ ] `quick/microphone.py` z funkcjami dla mikrofonów
  - [ ] `quick/utils.py` z pomocniczymi funkcjami
- [ ] Implementacja kluczowych funkcji:
  - [ ] `start_camera()` - automatyczne wykrywanie i uruchamianie kamery
  - [ ] `add_filter()` - dodawanie filtra do strumienia
  - [ ] `add_output()` - konfiguracja wyjścia (RTSP, zapis do pliku)
  - [ ] `save_config()` - zapisywanie konfiguracji do pliku YAML
  - [ ] `load_config()` - wczytywanie konfiguracji z pliku

## 6. Serwer Webowy
- [ ] Rozbudowa serwera webowego:
  - [ ] Obsługa HTTPS z automatycznymi certyfikatami
  - [ ] Konfiguracja dla domeny (np. kamera.rtaspi.pl)
  - [ ] Implementacja REST API z dokumentacją OpenAPI
- [ ] Utworzenie interfejsu webowego:
  - [ ] Panel zarządzania urządzeniami
  - [ ] Widok matrix dla kamer/mikrofonów
  - [ ] Kontrolki do konfiguracji i sterowania

## 7. Przetwarzanie Obrazu i Dźwięku
- [ ] Zaimplementować moduł przetwarzania obrazu:
  - [ ] Integracja z OpenCV w `processing/video/filters.py`
  - [ ] Implementacja podstawowych filtrów (`processing/video/filters.py`)
  - [ ] Detekcja obiektów/twarzy (`processing/video/detection.py`)
- [ ] Zaimplementować moduł przetwarzania dźwięku:
  - [ ] Integracja z bibliotekami audio w `processing/audio/filters.py`
  - [ ] Implementacja filtrów dźwięku (EQ, redukcja szumów)
  - [ ] Rozpoznawanie mowy (`processing/audio/speech.py`)
- [ ] System wykonywania pipeline'ów:
  - [ ] Implementacja `PipelineExecutor` w `processing/pipeline_executor.py`
  - [ ] Obsługa wielu źródeł danych
  - [ ] Dynamiczne ładowanie komponentów

## 8. DSL i Konfiguracja Pipelinów
- [x] Zaimplementować prosty DSL do definiowania pipeline'ów:
  - [x] Lekser w `dsl/lexer.py` (<150 linii)
  - [x] Parser w `dsl/parser.py` (<150 linii)
  - [x] Executor w `dsl/executor.py`
- [ ] System konfiguracji pipelinów z walidacją:
  - [ ] Parsery YAML/JSON z walidacją schematów
  - [ ] System watchera dla plików konfiguracyjnych (hot reload)
  - [ ] Zarządzanie zasobami (CPU/pamięć) w pipeline'ach



## 10. Testy Integracyjne
- [x] Rozbudować system testów:
  - [x] Testy jednostkowe dla nowych komponentów
  - [x] Testy integracyjne dla kluczowych funkcjonalności
  - [x] Testy wydajności streamingu
- [ ] Stworzyć środowisko testowe:
  - [ ] Symulatory urządzeń (kamery, mikrofony)
  - [ ] Wirtualne serwery RTSP/RTMP/WebRTC
  - [ ] Automacja testów w CI/CD

## 11. Wirtualne Urządzenia i Integracja z Przeglądarkę
- [ ] Implementacja wirtualnych urządzeń z zewnętrznych źródeł:
  - [ ] Stworzyć moduł `virtual_devices/` do zarządzania wirtualnymi urządzeniami
  - [ ] Funkcja montowania strumieni RTSP/RTMP/WebRTC jako wirtualnych urządzeń lokalnych
  - [ ] Obsługa prezentacji zdalnych kamer jako lokalne urządzenia widoczne w przeglądarce
  - [ ] Implementacja V4L2 loopback dla Linuxa
  - [ ] Implementacja DirectShow/Media Foundation dla Windows
  - [ ] Implementacja AVFoundation dla macOS
- [ ] Integracja z interfejsem przeglądarki:
  - [ ] Funkcja `mount_as_local_device(stream_url, device_name)` w API
  - [ ] Implementacja CLI: `rtaspi devices mount rtsp://example.com/stream`
  - [ ] Automatyczne wykrywanie zamontowanych urządzeń wirtualnych
  - [ ] Obsługa przełączania między rzeczywistym urządzeniem a zamontowanym wirtualnym
- [ ] Testowanie kompatybilności:
  - [ ] Weryfikacja widoczności wirtualnych urządzeń w popularnych przeglądarkach
  - [ ] Testy kompatybilności z aplikacjami komunikacyjnymi (Zoom, Teams, itp.)
  - [ ] Benchmark wydajności i opóźnień dla różnych protokołów

# Czy wszystkei pliki istniej?
.
├── CHANGELOG.md
├── config.yaml                  # Główny plik konfiguracyjny projektu
├── CONTRIBUTING.md
├── dist                         # Pliki dystrybucyjne
├── docs                         # Dokumentacja projektu
│   ├── api                      # Dokumentacja API
│   │   ├── core.md
│   │   ├── devices.md
│   │   ├── pipeline.md
│   │   └── streaming.md
│   ├── examples                 # Przykłady użycia
│   │   ├── basic_usage.md
│   │   ├── embedded_devices.md
│   │   └── filtering.md
│   ├── INSTALL.md
│   ├── PROJECTS.md
│   ├── README.md
│   └── tutorials                # Tutoriale
│       ├── beginner
│       ├── advanced
│       └── embedded
├── examples                     # Przykłady kodu
│   ├── basic                    # Podstawowe przykłady użycia
│   │   ├── camera_stream.py
│   │   ├── device_discovery.py
│   │   └── microphone_stream.py
│   ├── embedded                 # Przykłady dla urządzeń embedded
│   │   ├── raspberry_pi
│   │   ├── radxa
│   │   └── jetson_nano
│   ├── pipelines                # Przykłady przetwarzania
│   │   ├── face_detection.py
│   │   ├── motion_detection.py
│   │   └── object_tracking.py
│   ├── speech                   # Przykłady przetwarzania mowy
│   │   ├── speech_to_text.py
│   │   ├── text_to_speech.py
│   │   ├── realtime_translation.py
│   │   └── voice_assistant.py
│   └── webserver                # Przykłady serwera webowego
│       ├── https_server.py
│       └── matrix_view.py
├── LICENSE
├── Makefile
├── pyproject.toml              # Konfiguracja projektu Python
├── README.md
├── requirements.txt
├── rtaspi.config.yaml          # Główna konfiguracja rtaspi
├── rtaspi.devices.yaml         # Konfiguracja urządzeń
├── rtaspi.pipeline.yaml        # Konfiguracja pipelinów przetwarzania
├── rtaspi.secrets.yaml         # Poufne dane (hasła, klucze)
├── rtaspi.streams.yaml         # Konfiguracja strumieni
├── scripts                     # Skrypty pomocnicze
│   ├── configure_hardware.sh
│   ├── install_models.sh
│   ├── optimize_rpi.sh
│   ├── publish.sh
│   ├── setup_service.sh
│   └── upgrade.sh
├── service                     # Skrypty serwisowe
│   ├── start.sh
│   └── stop.sh
├── setup.py
├── src
│   └── rtaspi
│       ├── api                 # Publiczne API biblioteki
│       │   ├── devices.py      # Fasada do zarządzania urządzeniami
│       │   ├── __init__.py
│       │   ├── pipelines.py    # Fasada do zarządzania pipelinami
│       │   ├── server.py       # Fasada do zarządzania serwerem
│       │   ├── speech.py       # Fasada do funkcji mowy
│       │   └── streams.py      # Fasada do zarządzania strumieniami
│       ├── cli                 # Interfejs linii poleceń
│       │   ├── commands        # Implementacje komend
│       │   │   ├── config.py
│       │   │   ├── devices.py
│       │   │   ├── __init__.py
│       │   │   ├── pipelines.py
│       │   │   ├── server.py
│       │   │   ├── speech.py   # Komendy do przetwarzania mowy
│       │   │   └── streams.py
│       │   ├── completion      # Autouzupełnianie dla shella
│       │   │   ├── bash.sh
│       │   │   ├── fish.fish
│       │   │   └── zsh.zsh
│       │   ├── __init__.py
│       │   └── shell.py        # Główny punkt wejścia CLI
│       ├── config              # Konfiguracja
│       │   ├── __init__.py
│       │   ├── schema.py       # Schematy konfiguracji
│       │   └── validators.py   # Walidatory konfiguracji
│       ├── constants           # Stałe i enumeracje
│       │   ├── devices.py      # Typy urządzeń (DeviceType)
│       │   ├── filters.py      # Typy filtrów (FilterType)
│       │   ├── __init__.py
│       │   ├── outputs.py      # Typy wyjść (OutputType)
│       │   ├── protocols.py    # Typy protokołów (ProtocolType)
│       │   └── speech.py       # Stałe związane z mową
│       ├── core                # Podstawowe komponenty
│       │   ├── config.py       # Zarządzanie konfiguracją
│       │   ├── defaults.py     # Domyślne wartości konfiguracji
│       │   ├── __init__.py
│       │   ├── logging.py      # System logowania
│       │   ├── mcp.py          # Broker komunikacji (MCP)
│       │   └── utils.py        # Narzędzia pomocnicze
│       ├── device_managers     # Zarządzanie urządzeniami
│       │   ├── auth            # Autoryzacja urządzeń
│       │   │   ├── basic.py
│       │   │   ├── digest.py
│       │   │   └── __init__.py
│       │   ├── base.py         # Klasa bazowa managera urządzeń
│       │   ├── discovery       # Wykrywanie urządzeń
│       │   │   ├── __init__.py
│       │   │   ├── mdns.py
│       │   │   ├── onvif.py
│       │   │   └── upnp.py
│       │   ├── __init__.py
│       │   ├── local_devices.py # Manager urządzeń lokalnych
│       │   ├── network_devices.py # Manager urządzeń sieciowych
│       │   └── protocols       # Obsługa protokołów
│       │       ├── __init__.py
│       │       ├── http.py
│       │       ├── rtmp.py
│       │       ├── rtsp.py
│       │       └── webrtc.py
│       ├── dsl                 # Domain Specific Language
│       │   ├── executor.py     # Wykonanie definicji DSL
│       │   ├── __init__.py
│       │   ├── lexer.py        # Lekser DSL
│       │   └── parser.py       # Parser DSL
│       ├── __init__.py
│       ├── __main__.py
│       ├── processing          # Przetwarzanie audio/video
│       │   ├── audio           # Przetwarzanie audio
│       │   │   ├── filters.py  # Filtry audio (EQ, denoise)
│       │   │   ├── __init__.py
│       │   │   ├── playback.py # Odtwarzanie audio
│       │   │   ├── recording.py # Nagrywanie audio
│       │   │   └── speech.py   # Detekcja mowy
│       │   ├── __init__.py
│       │   ├── pipeline_executor.py # Wykonawca pipelinów
│       │   └── video           # Przetwarzanie video
│       │       ├── detection.py
│       │       ├── filters.py
│       │       └── __init__.py
│       ├── quick               # Uproszczone API dla juniorów
│       │   ├── camera.py       # Proste funkcje do kamer
│       │   ├── __init__.py
│       │   ├── microphone.py   # Proste funkcje do mikrofonów
│       │   ├── speech.py       # Proste funkcje do mowy
│       │   └── utils.py        # Pomocnicze funkcje
│       ├── schemas             # Schematy danych
│       │   ├── device.py
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   ├── speech.py       # Schematy danych dla mowy
│       │   └── stream.py
│       ├── speech              # Moduł przetwarzania mowy
│       │   ├── engines         # Silniki rozpoznawania mowy
│       │   │   ├── google.py   # Integracja z Google Speech API
│       │   │   ├── __init__.py
│       │   │   ├── local.py    # Lokalne silniki (Vosk, Whisper)
│       │   │   └── mozilla.py  # Integracja z Mozilla DeepSpeech
│       │   ├── __init__.py     
│       │   ├── stt.py          # Speech-to-Text
│       │   ├── tts.py          # Text-to-Speech
│       │   ├── translation.py  # Tłumaczenie mowy
│       │   ├── virtual_mic.py  # Wirtualny mikrofon (TTS->stream)
│       │   └── virtual_speaker.py # Wirtualny głośnik (STT->file)
│       ├── streaming           # Obsługa strumieni
│       │   ├── adapters        # Adaptery do różnych implementacji
│       │   │   ├── ffmpeg.py
│       │   │   ├── gstreamer.py
│       │   │   └── __init__.py
│       │   ├── codec_handlers  # Obsługa kodeków
│       │   │   ├── audio.py
│       │   │   ├── __init__.py
│       │   │   └── video.py
│       │   ├── __init__.py
│       │   ├── rtmp.py         # Serwer RTMP
│       │   ├── rtsp.py         # Serwer RTSP
│       │   ├── stream_config.py # Konfiguracja strumieni
│       │   ├── utils.py        # Narzędzia do streamingu
│       │   └── webrtc.py       # Serwer WebRTC
│       ├── utils               # Narzędzia pomocnicze
│       │   ├── decorators.py   # Dekoratory
│       │   ├── format.py       # Formatowanie danych
│       │   ├── __init__.py
│       │   ├── network.py      # Funkcje sieciowe
│       │   └── process.py      # Zarządzanie procesami
│       ├── virtual_devices     # Moduł urządzeń wirtualnych
│       │   ├── __init__.py
│       │   ├── linux           # Wsparcie dla Linux (V4L2)
│       │   │   ├── __init__.py
│       │   │   └── v4l2loopback.py
│       │   ├── macos           # Wsparcie dla macOS (AVFoundation)
│       │   │   ├── avfoundation.py
│       │   │   └── __init__.py
│       │   ├── manager.py      # Manager wirtualnych urządzeń
│       │   └── windows         # Wsparcie dla Windows
│       │       ├── directshow.py
│       │       ├── __init__.py
│       │       └── mediafoundation.py
│       └── _version.py         # Wersja biblioteki
├── storage                     # Katalog przechowywania danych
│   ├── local_streams
│   ├── logs
│   ├── network_devices.json
│   ├── network_streams
│   └── speech                  # Katalog na dane mowy
│       ├── models              # Modele do rozpoznawania mowy
│       ├── recordings          # Nagrania mowy
│       └── transcripts         # Transkrypcje
└── tests                       # Testy
    ├── conftest.py
    ├── __init__.py
    ├── test_api                # Testy API
    │   ├── test_devices.py
    │   ├── test_pipelines.py
    │   ├── test_speech.py      # Testy API mowy
    │   └── test_streams.py
    ├── test_cli                # Testy CLI
    │   ├── test_shell.py
    │   └── test_speech_commands.py # Testy komend mowy
    ├── test_discovery.py
    ├── test_dsl                # Testy DSL
    │   ├── test_executor.py
    │   └── test_parser.py
    ├── test_local_devices.py
    ├── test_network_devices.py
    ├── test_processing         # Testy przetwarzania
    │   ├── test_audio.py
    │   ├── test_speech.py      # Testy przetwarzania mowy
    │   └── test_video.py
    ├── test_quick              # Testy uproszczonego API
    │   ├── test_camera.py
    │   └── test_speech.py      # Testy Quick API dla mowy
    ├── test_speech             # Testy modułu mowy
    │   ├── test_stt.py         # Testy Speech-to-Text
    │   ├── test_tts.py         # Testy Text-to-Speech
    │   └── test_virtual_devices.py # Testy wirtualnych urządzeń mowy
    ├── test_streaming.py
    └── test_virtual_devices    # Testy urządzeń wirtualnych
        ├── test_linux.py
        ├── test_macos.py
        └── test_windows.py

