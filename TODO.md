# Uporządkowana Lista Zadań (TODO)

## 1. Refaktoryzacja i Poprawa Kodu
- [ ] Stworzyć modularną strukturę w `src/rtaspi/`:
  - [ ] Uporządkować klasy i funkcje w `device_managers/` dla lepszego reużycia kodu
  - [ ] Przeorganizować kod w `streaming/` (rtsp.py, rtmp.py, webrtc.py) dla większej spójności
  - [ ] Wyodrębnić wspólne funkcjonalności do klas bazowych
- [ ] Zaktualizować testy jednostkowe po refaktoryzacji
  - [ ] Zapewnić, że istniejące testy przechodzą (test_discovery.py, test_local_devices.py, test_network_devices.py, test_streaming.py)

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
- [ ] Stworzyć system konfiguracji strumieni w formatach:
  - [ ] YAML
  - [ ] JSON
- [ ] Zaimplementować własny DSL (Domain Specific Language) do definiowania pipelines
  - [ ] Parser DSL
  - [ ] Executor dla zdefiniowanych pipelines

## 9. Dokumentacja
- [ ] Przygotować szczegółową dokumentację API
- [ ] Stworzyć przykłady konfiguracji dla różnych scenariuszy użycia
- [ ] Opisać dostępne protokoły i metody komunikacji