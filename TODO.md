# Zaktualizowana Lista Zadań (TODO)

## 1. Refaktoryzacja i Struktura Kodu
- [x] Utworzenie nowej struktury katalogów:
  - [x] Stworzyć nowe katalogi: `api/`, `cli/`, `constants/`, `quick/`, `processing/`, `schemas/`
  - [x] Przeorganizować istniejące katalogi: `device_managers/`, `streaming/`
  - [x] Przygotować pliki `__init__.py` dla wszystkich modułów
- [x] Implementacja centralnego systemu stałych i enumeracji:
  - [x] Stworzyć `constants/filters.py` z `FilterType` (GRAYSCALE, EDGE_DETECTION, FACE_DETECTION, itd.)
  - [x] Stworzyć `constants/devices.py` z `DeviceType` (CAMERA, MICROPHONE, NETWORK_CAMERA, itd.)
  - [x] Stworzyć `constants/outputs.py` z `OutputType` (RTSP, RTMP, FILE, EVENT, itd.)
  - [x] Stworzyć `constants/protocols.py` z `ProtocolType` (HTTP, RTSP, RTMP, WEBRTC, itd.)
- [x] Podział dużych plików na mniejsze moduły:
  - [x] Podzielić pliki większe niż 300 linii kodu
  - [x] Wydzielić wspólne funkcjonalności do klas bazowych i modułów pomocniczych
  - [x] Zapewnić kompatybilność wsteczną

## 2. System Konfiguracji
- [ ] Zaimplementować hierarchiczny system konfiguracji:
  - [ ] Domyślna konfiguracja w kodzie (`src/rtaspi/core/defaults.py`)
  - [ ] Globalna konfiguracja (`rtaspi.config.yaml`)
  - [ ] Konfiguracja użytkownika (`~/.config/rtaspi/config.yaml`)
  - [ ] Konfiguracja projektu (`.rtaspi/config.yaml`)
  - [ ] Obsługa zmiennych środowiskowych (`.env`)
- [x] Utworzyć schematy danych dla walidacji konfiguracji:
  - [x] Zdefiniować `schemas/device.py` dla urządzeń
  - [x] Zdefiniować `schemas/stream.py` dla strumieni
  - [x] Zdefiniować `schemas/pipeline.py` dla pipelinów przetwarzania
- [ ] Implementacja `ConfigManager` z metodami:
  - [ ] `get_config(section, key, default=None)`
  - [ ] `set_config(section, key, value, level='user')`
  - [ ] `load_config_file(path)`
  - [ ] `save_config_file(path, level='user')`

## 3. Interfejs Wiersza Poleceń (CLI)
- [x] Zaimplementować główny szkielet CLI:
  - [x] Utworzyć klasę `RTASPIShell` w `src/rtaspi/cli/shell.py`
  - [x] Zintegrować z biblioteką `click` do obsługi parametrów
  - [x] Dodać obsługę globalnych opcji (--config, --verbose, --help)
- [x] Implementacja podkomend dla CLI:
  - [x] `cli/commands/config.py` - zarządzanie konfiguracją
  - [x] `cli/commands/devices.py` - zarządzanie urządzeniami
  - [x] `cli/commands/streams.py` - zarządzanie strumieniami
  - [x] `cli/commands/pipelines.py` - zarządzanie pipelinami
  - [x] `cli/commands/server.py` - zarządzanie serwerem
- [x] Dodanie autouzupełniania dla powłok:
  - [x] Bash completion
  - [x] Zsh completion
  - [x] Fish completion

## 4. API Biblioteki
- [x] Zaimplementować publiczne API biblioteki:
  - [x] `api/devices.py` - fasada do zarządzania urządzeniami
  - [x] `api/streams.py` - fasada do zarządzania strumieniami
  - [x] `api/pipelines.py` - fasada do zarządzania pipelinami
  - [x] `api/server.py` - fasada do zarządzania serwerem webowym
- [ ] Zapewnić spójność między API a CLI (używanie tych samych fasad)
- [ ] Dodać obszerne docstringi z przykładami użycia

## 5. Uproszczone API dla Juniorów
- [x] Stworzyć moduł `quick/` z prostymi interfejsami:
  - [x] `quick/camera.py` z funkcjami dla kamer
  - [x] `quick/microphone.py` z funkcjami dla mikrofonów
  - [x] `quick/utils.py` z pomocniczymi funkcjami
- [ ] Implementacja kluczowych funkcji:
  - [ ] `start_camera()` - automatyczne wykrywanie i uruchamianie kamery
  - [ ] `add_filter()` - dodawanie filtra do strumienia
  - [ ] `add_output()` - konfiguracja wyjścia (RTSP, zapis do pliku)
  - [ ] `save_config()` - zapisywanie konfiguracji do pliku YAML
  - [ ] `load_config()` - wczytywanie konfiguracji z pliku

## 6. Serwer Webowy
- [x] Rozbudowa serwera webowego:
  - [x] Obsługa HTTPS z automatycznymi certyfikatami
  - [x] Konfiguracja dla domeny (np. kamera.rtaspi.pl)
  - [x] Implementacja REST API z dokumentacją OpenAPI
- [ ] Utworzenie interfejsu webowego:
  - [ ] Panel zarządzania urządzeniami
  - [ ] Widok matrix dla kamer/mikrofonów
  - [ ] Kontrolki do konfiguracji i sterowania

## 7. Przetwarzanie Obrazu i Dźwięku
- [x] Zaimplementować moduł przetwarzania obrazu:
  - [x] Integracja z OpenCV w `processing/video/filters.py`
  - [x] Implementacja podstawowych filtrów (`processing/video/filters.py`)
  - [x] Detekcja obiektów/twarzy (`processing/video/detection.py`)
- [x] Zaimplementować moduł przetwarzania dźwięku:
  - [x] Integracja z bibliotekami audio w `processing/audio/filters.py`
  - [x] Implementacja filtrów dźwięku (EQ, redukcja szumów)
  - [x] Rozpoznawanie mowy (`processing/audio/speech.py`)
- [x] System wykonywania pipeline'ów:
  - [x] Implementacja `PipelineExecutor` w `processing/pipeline_executor.py`
  - [x] Obsługa wielu źródeł danych
  - [x] Dynamiczne ładowanie komponentów

## 8. DSL i Konfiguracja Pipelinów
- [x] Zaimplementować prosty DSL do definiowania pipeline'ów:
  - [x] Lekser w `dsl/lexer.py` (<150 linii)
  - [x] Parser w `dsl/parser.py` (<150 linii)
  - [x] Executor w `dsl/executor.py`
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

## 12. Dokumentacja
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
