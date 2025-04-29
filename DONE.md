# TODO - Lista Zadań 

## 1. Refaktoryzacja i Struktura Kodu
- [ ] Utworzenie nowej struktury katalogów:
  - [ ] Stworzyć nowe katalogi: `api/`, `cli/`, `constants/`, `quick/`, `processing/`, `schemas/`
  - [x] Przeorganizować istniejące katalogi: `device_managers/`, `streaming/`
  - [x] Przygotować pliki `__init__.py` dla wszystkich modułów
- [ ] Implementacja centralnego systemu stałych i enumeracji:
  - [ ] Stworzyć `constants/filters.py` z `FilterType` (GRAYSCALE, EDGE_DETECTION, FACE_DETECTION, itd.)
  - [ ] Stworzyć `constants/devices.py` z `DeviceType` (CAMERA, MICROPHONE, NETWORK_CAMERA, itd.)
  - [ ] Stworzyć `constants/outputs.py` z `OutputType` (RTSP, RTMP, FILE, EVENT, itd.)
  - [ ] Stworzyć `constants/protocols.py` z `ProtocolType` (HTTP, RTSP, RTMP, WEBRTC, itd.)
- [ ] Podział dużych plików na mniejsze moduły:
  - [ ] Podzielić pliki większe niż 400 linii kodu
  - [ ] Wydzielić wspólne funkcjonalności do klas bazowych i modułów pomocniczych
  - [ ] Zapewnić kompatybilność wsteczną

## 2. System Konfiguracji
- [x] Zaimplementować hierarchiczny system konfiguracji:
  - [x] Domyślna konfiguracja w kodzie (`src/rtaspi/core/defaults.py`)
  - [x] Globalna konfiguracja (`rtaspi.config.yaml`)
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

## 3. Interfejs Wiersza Poleceń (CLI)
- [ ] Zaimplementować główny szkielet CLI:
  - [ ] Utworzyć klasę `RTASPIShell` w `src/rtaspi/cli/shell.py`
  - [ ] Zintegrować z biblioteką `click` do obsługi parametrów
  - [ ] Dodać obsługę globalnych opcji (--config, --verbose, --help)
- [ ] Implementacja podkomend dla CLI:
  - [ ] `cli/commands/config.py` - zarządzanie konfiguracją
  - [ ] `cli/commands/devices.py` - zarządzanie urządzeniami
  - [ ] `cli/commands/streams.py` - zarządzanie strumieniami
  - [ ] `cli/commands/pipelines.py` - zarządzanie pipelinami
  - [ ] `cli/commands/server.py` - zarządzanie serwerem
- [ ] Dodanie autouzupełniania dla powłok:
  - [ ] Bash completion
  - [ ] Zsh completion
  - [ ] Fish completion

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
- [ ] Zaimplementować prosty DSL do definiowania pipeline'ów:
  - [ ] Lekser w `dsl/lexer.py` (<150 linii)
  - [ ] Parser w `dsl/parser.py` (<150 linii)
  - [ ] Executor w `dsl/executor.py`
- [ ] System konfiguracji pipelinów z walidacją:
  - [ ] Parsery YAML/JSON z walidacją schematów
  - [ ] System watchera dla plików konfiguracyjnych (hot reload)
  - [ ] Zarządzanie zasobami (CPU/pamięć) w pipeline'ach

## 9. Wsparcie dla Urządzeń Embedded
- [x] Utworzyć konfiguracje dla popularnych platform:
  - [x] Raspberry Pi (różne modele)
  - [x] Radxa
  - [x] Jetson Nano
- [x] Zautomatyzować inicjalizację i konfigurację:
  - [x] Wykrywanie sprzętu
  - [x] Automatyczna konfiguracja zależności
  - [x] Optymalizacja dla ograniczonych zasobów
- [x] Przygotować skrypty instalacyjne:
  - [x] Obraz systemowy z prekonfigurowaną biblioteką
  - [x] Skrypty automatyzujące instalację

## 10. Testy Integracyjne
- [x] Rozbudować system testów:
  - [x] Testy jednostkowe dla nowych komponentów
  - [x] Testy integracyjne dla kluczowych funkcjonalności
  - [x] Testy wydajności streamingu
- [x] Stworzyć środowisko testowe:
  - [x] Symulatory urządzeń (kamery, mikrofony)
  - [x] Wirtualne serwery RTSP/RTMP/WebRTC
  - [x] Automacja testów w CI/CD

## 11. Dokumentacja docs/
- [x] Przygotować kompletną dokumentację:
  - [x] Referencja API
  - [x] Poradnik użytkownika
  - [x] Tutoriale dla różnych poziomów zaawansowania
- [x] Stworzyć przykłady:
  - [x] Podstawowe przykłady użycia
  - [x] Przykłady dla urządzeń embedded
  - [x] Zaawansowane przykłady integracji
- [x] Dokumentacja przetwarzania:
  - [x] Przewodniki po dostępnych filtrach
  - [x] Integracja z OpenCV i bibliotekami audio
  - [x] Tworzenie własnych komponentów przetwarzania

## Oczekiwana struktura plików

```
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
│       │   └── streams.py      # Fasada do zarządzania strumieniami
│       ├── cli                 # Interfejs linii poleceń
│       │   ├── commands        # Implementacje komend
│       │   │   ├── config.py
│       │   │   ├── devices.py
│       │   │   ├── __init__.py
│       │   │   ├── pipelines.py
│       │   │   ├── server.py
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
│       │   └── protocols.py    # Typy protokołów (ProtocolType)
│       ├── core                # Podstawowe komponenty
│       │   ├── config.py       # Zarządzanie konfiguracją
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
│       │   │   ├── filters.py
│       │   │   ├── __init__.py
│       │   │   └── speech.py
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
│       │   └── utils.py        # Pomocnicze funkcje
│       ├── schemas             # Schematy danych
│       │   ├── device.py
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   └── stream.py
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
│       └── _version.py         # Wersja biblioteki
├── storage                     # Katalog przechowywania danych
│   ├── local_streams
│   ├── logs
│   ├── network_devices.json
│   └── network_streams
└── tests                       # Testy
    ├── conftest.py
    ├── __init__.py
    ├── test_api                # Testy API
    │   ├── test_devices.py
    │   ├── test_pipelines.py
    │   └── test_streams.py
    ├── test_cli                # Testy CLI
    │   └── test_shell.py
    ├── test_discovery.py
    ├── test_dsl                # Testy DSL
    │   ├── test_executor.py
    │   └── test_parser.py
    ├── test_local_devices.py
    ├── test_network_devices.py
    ├── test_processing         # Testy przetwarzania
    │   ├── test_audio.py
    │   └── test_video.py
    ├── test_quick              # Testy uproszczonego API
    │   └── test_camera.py
    └── test_streaming.py
```

## Plan

Szczegółowy Plan Refaktoryzacji i Objaśnienie Struktury

## Główne Zmiany w Strukturze Projektu

Po analizie obecnej struktury projektu, zaproponowałem finalną strukturę, która łączy modularność i reużywalność z przyjaznością dla programistów juniorów. Oto najważniejsze zmiany:

### 1. Wprowadzenie Katalogów Funkcjonalnych

- **src/rtaspi/api/** - Publiczny interfejs API biblioteki, fasady do wszystkich funkcjonalności
- **src/rtaspi/cli/** - Interfejs linii poleceń (CLI) do obsługi przez shell
- **src/rtaspi/constants/** - Centralny punkt definicji stałych i enumeracji
- **src/rtaspi/quick/** - Uproszczone API dla juniorów, ukrywające złożoność
- **src/rtaspi/processing/** - Przetwarzanie audio/video z podziałem na moduły
- **src/rtaspi/schemas/** - Schematy danych używane w całej aplikacji

### 2. Reorganizacja Istniejących Modułów

- **device_managers/** - Dodanie podkatalogów `auth/`, `discovery/` i `protocols/`
- **streaming/** - Dodanie podkatalogów `adapters/` i `codec_handlers/`
- **core/** - Pozostawiono bez większych zmian jako fundament systemu

### 3. Strukturyzacja Dokumentacji i Przykładów

- **docs/** - Podzielono na `api/`, `examples/` i `tutorials/` z naciskiem na różne poziomy zaawansowania
- **examples/** - Rozbudowano z praktycznymi przykładami dla różnych zastosowań i urządzeń

## Korzyści z Nowej Struktury

### Dla Programistów Juniorów

1. **Uproszczone API** (`rtaspi.quick`):
   - Proste funkcje jak `start_camera()`, `add_filter()` z pełnym wsparciem IDE
   - Enumeracje zapewniające podpowiedzi i zapobiegające błędom

2. **Czytelna Dokumentacja**:
   - Dedykowane tutoriale dla początkujących (`docs/tutorials/beginner`)
   - Proste przykłady w katalogu `examples/basic`

3. **Struktury Konfiguracyjne**:
   - Standardowe formaty (YAML, JSON) z jasnymi schematami
   - Przykłady gotowe do użycia

### Dla Zaawansowanych Programistów

1. **Modułowość i Rozszerzalność**:
   - Jasno określone interfejsy między komponentami
   - Możliwość wymiany implementacji za pomocą systemu adapterów

2. **Kompletne API**:
   - Pełen dostęp do wszystkich funkcjonalności przez spójne interfejsy
   - Możliwość integracji z własnymi systemami

3. **DSL do Zaawansowanej Konfiguracji**:
   - Własny język do definiowania złożonych pipeline'ów przetwarzania
   - Elastyczna definicja przepływu danych

### Wspólne Korzyści

1. **Spójność**:
   - Jednolite konwencje nazewnictwa
   - Te same struktury danych używane we wszystkich interfejsach

2. **Testowalność**:
   - Mniejsze, wyspecjalizowane komponenty łatwiejsze do testowania
   - Struktura katalogów testów odzwierciedlająca strukturę kodu

3. **Dopasowanie do Urządzeń Embedded**:
   - Optymalizacja dla zasobów ograniczonych
   - Dedykowane przykłady i konfiguracje dla popularnych platform

## Plan Implementacji Refaktoryzacji

Aby zminimalizować ryzyko i zapewnić ciągłość działania, refaktoryzacja powinna przebiegać w następujących etapach:

### Etap 1: Fundamenty

1. Utworzenie nowej struktury katalogów
2. Definicja stałych i enumeracji w `constants/`
3. Implementacja schematów danych w `schemas/`
4. Reorganizacja kodu core bez zmiany funkcjonalności

### Etap 2: Modularyzacja

1. Ekstrakcja wspólnego kodu do reużywalnych komponentów
2. Podział dużych plików na mniejsze, wyspecjalizowane moduły
3. Implementacja interfejsów i klas bazowych
4. Aktualizacja istniejących testów

### Etap 3: Interfejsy

1. Implementacja publicznego API w `api/`
2. Utworzenie interfejsu CLI w `cli/`
3. Rozwój uproszczonego API w `quick/`
4. Dodanie nowych testów dla interfejsów

### Etap 4: Dokumentacja i Przykłady

1. Aktualizacja dokumentacji
2. Rozwój przykładów
3. Przygotowanie tutoriali
4. Finalne testy integracyjne

## Wnioski

Proponowana struktura łączy zalety modularnego, rozszerzalnego systemu z przyjaznością dla początkujących programistów. Wprowadzenie stałych i enumeracji zamiast literałów tekstowych znacząco podnosi użyteczność biblioteki, zapewniając podpowiedzi IDE i zmniejszając ryzyko błędów.

Dodanie uproszczonego interfejsu `rtaspi.quick` pozwoli programistom juniorom na szybkie rozpoczęcie pracy z biblioteką, jednocześnie dając im możliwość nauki i stopniowego przechodzenia do bardziej zaawansowanych funkcjonalności w miarę zdobywania doświadczenia.

Jednocześnie, biblioteka zachowuje pełną moc i elastyczność dla zaawansowanych użytkowników, którzy mogą korzystać z pełnego API, DSL i możliwości konfiguracyjnych.
