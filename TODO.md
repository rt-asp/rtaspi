# TODO - Lista Zadań

## 1. Refaktoryzacja i Poprawa Kodu
- [ ] Podzielić kod na mniejsze, reużywalne komponenty (zasada pojedynczej odpowiedzialności):
  - [ ] Rozbić duże pliki na moduły o maksymalnej wielkości 300 linii
  - [ ] Zapewnić, że każda klasa/funkcja ma jedną, jasno określoną odpowiedzialność
  - [ ] Stosować zasadę DRY (Don't Repeat Yourself) dla powtarzającego się kodu
- [ ] Refaktoryzacja w `src/rtaspi/device_managers/`:
  - [ ] Utworzyć folder `protocols/` z oddzielnymi klasami dla każdego protokołu
  - [ ] Wydzielić logikę autoryzacji i autentykacji do oddzielnego modułu `auth/`
  - [ ] Przenieść metody wykrywania urządzeń do wyspecjalizowanych klas w `discovery/`
- [ ] Refaktoryzacja w `src/rtaspi/streaming/`:
  - [ ] Stworzyć wspólny interfejs `BaseStreamingServer` dla wszystkich serwerów
  - [ ] Wyodrębnić logikę konfiguracji strumieni do `stream_config.py`
  - [ ] Wydzielić obsługę kodowania/dekodowania do modułu `codec_handlers/`
  - [ ] Stworzyć moduł `adapters/` do integracji z różnymi implementacjami streamingu
- [ ] Utworzyć nowy moduł `src/rtaspi/utils/`:
  - [ ] Przenieść wspólne funkcje pomocnicze do dedykowanych plików (`network.py`, `process.py`, `format.py`)
  - [ ] Stworzyć reużywalne dekoratory do obsługi błędów, logowania, cache w `decorators.py`
- [ ] Zaktualizować testy jednostkowe po refaktoryzacji:
  - [ ] Zapewnić, że istniejące testy przechodzą (test_discovery.py, test_local_devices.py, test_network_devices.py, test_streaming.py)
  - [ ] Dodać testy dla nowo utworzonych, mniejszych komponentów
  - [ ] Wykorzystać wzorzec AAA (Arrange-Act-Assert) w testach

## 2. Rozbudowa Serwera Webowego
- [ ] Dodać obsługę HTTPS dla domeny kamera.rtaspi.pl
  - [ ] Zaimplementować automatyczną konfigurację certyfikatów SSL
  - [ ] Skonfigurować przekierowanie HTTP na HTTPS
- [ ] Stworzyć podstawowy interfejs webowy do zarządzania urządzeniami
  - [ ] Panel konfiguracyjny dla urządzeń lokalnych i sieciowych
  - [ ] Widok podglądu strumieni z kamer i mikrofonów

## 3. Przykłady Użycia
- [ ] Stworzyć folder `examples/` z przykładami implementacji:
  - [ ] Przykład przeglądania lokalnej kamery przez RTMP
  - [ ] Przykład przeglądania lokalnej kamery przez WebRTC
  - [ ] Przykład obsługi mikrofonu i głośnika
- [ ] Przygotować dokumentację do przykładów z instrukcjami uruchomienia

## 4. Wsparcie dla Urządzeń Embedded
- [ ] Stworzyć automatyczną inicjalizację dla urządzeń typu:
  - [ ] Raspberry Pi
  - [ ] Radxa
  - [ ] Inne popularne platformy embedded
- [ ] Przygotować prekonfigurowane obrazy lub skrypty instalacyjne
- [ ] Dodać automatyczne wykrywanie sprzętu

## 5. Testy Integracyjne
- [ ] Zaimplementować testy dla protokołów:
  - [ ] RTMP
  - [ ] WebRTC
  - [ ] HTTP/HTTPS
- [ ] Stworzyć środowisko testowe symulujące różne urządzenia
- [ ] Dodać testy wydajności strumieni audio/video

## 6. Obsługa Urządzeń Audio/Video
- [ ] Stworzyć interfejs do zarządzania urządzeniami w przeglądarce:
  - [ ] Widok matrix kamer, mikrofonów i głośników
  - [ ] Kontrolki głośności i parametrów strumieni
- [ ] Zaimplementować miksowanie strumieni audio
  - [ ] Kierowanie dźwięku z kamer do głośników
  - [ ] Miksowanie wielu źródeł audio

## 7. Zaawansowana Obsługa Strumieni
- [ ] Umożliwić tworzenie strumieni RTSP/RTMP z różnych źródeł:
  - [ ] Mikrofon z komputera
  - [ ] Kamery LAN
  - [ ] Inne źródła multimediów
- [ ] Dodać obsługę różnych formatów i kodeków

## 8. DSL i Konfiguracja Pipelines
- [ ] Stworzyć system konfiguracji strumieni z minimalistycznym podejściem:
  - [ ] Implementacja parsera YAML z obsługą tylko niezbędnych opcji
  - [ ] Implementacja parsera JSON z takim samym zestawem opcji
  - [ ] Walidator konfiguracji sprawdzający poprawność parametrów
- [ ] Implementacja małych, niezależnych komponentów dla DSL:
  - [ ] Prosty lekser i parser (każdy <150 linii kodu)
  - [ ] Biblioteka standardowych komponentów DSL (filtry, źródła, wyjścia)
  - [ ] System rozszerzeń DSL do dodawania własnych komponentów
- [ ] Executor dla zdefiniowanych pipelines:
  - [ ] Rozdzielenie logiki na mniejsze komponenty (loader, validator, executor)
  - [ ] Obsługa watchwatchera dla plików konfiguracyjnych (hot reload)
  - [ ] Mechanizm zarządzania zasobami (przydział CPU/pamięci dla każdego kroku)

## 9. Przetwarzanie Obrazu z OpenCV
- [ ] Stworzyć moduł integracyjny z OpenCV
  - [ ] Dodać klasy do przetwarzania obrazu w czasie rzeczywistym
  - [ ] Zaimplementować podstawowe filtry (rozmycie, wyostrzenie, detekcja krawędzi)
  - [ ] Dodać zaawansowane przetwarzanie (detekcja twarzy, obiektów, ruchu)
- [ ] Stworzyć system wtyczek (plugins) dla własnych algorytmów CV
  - [ ] Definiowanie własnych filtrów w Pythonie
  - [ ] Integracja z istniejącymi projektami OpenCV
- [ ] Umożliwić konfigurację przetwarzania obrazu przez:
  - [ ] API Pythona
  - [ ] Pliki YAML/JSON
  - [ ] DSL (ten sam co dla pipelines)

## 10. Przetwarzanie Audio
- [ ] Zintegrować biblioteki do przetwarzania dźwięku
  - [ ] PyAudio do niskopoziomowej obróbki
  - [ ] Librosa do analizy dźwięku
  - [ ] SoundFile do obsługi różnych formatów
- [ ] Zaimplementować podstawowe operacje na dźwięku:
  - [ ] Filtrowanie (EQ, redukcja szumów)
  - [ ] Detekcja mowy/dźwięku
  - [ ] Kompresja i normalizacja głośności
- [ ] Umożliwić konfigurację przetwarzania audio przez:
  - [ ] API Pythona
  - [ ] Pliki YAML/JSON
  - [ ] DSL (ten sam co dla pipelines)

## 11. Integracja z AI i ML
- [ ] Dodać wsparcie dla modeli uczenia maszynowego
  - [ ] Integracja z TensorFlow/PyTorch
  - [ ] Obsługa modeli ONNX
  - [ ] Optymalizacja dla urządzeń embedded (TensorFlow Lite)
- [ ] Zaimplementować przykładowe modele:
  - [ ] Detekcja i klasyfikacja obiektów
  - [ ] Rozpoznawanie mowy
  - [ ] Segmentacja semantyczna obrazu
- [ ] Stworzyć system dołączania własnych modeli ML

## 12. Moduł Adnotacji i Metadanych
- [ ] Zaimplementować system dodawania metadanych do strumieni
  - [ ] Adnotacje w czasie rzeczywistym (znaczniki, bounding boxy)
  - [ ] Zapisywanie wyników analizy (detekcji, klasyfikacji)
  - [ ] Timestampy i geolokalizacja
- [ ] Stworzyć API do odczytu i zapisu metadanych
  - [ ] Zarządzanie metadanymi przez REST API
  - [ ] Zapisywanie metadanych do bazy danych
  - [ ] Eksport metadanych w formatach standardowych

## 13. Dokumentacja w folderze docs/
- [ ] Przygotować szczegółową dokumentację API
- [ ] Stworzyć przykłady konfiguracji dla różnych scenariuszy użycia
- [ ] Opisać dostępne protokoły i metody komunikacji
- [ ] Dodać tutoriale przetwarzania obrazu i dźwięku