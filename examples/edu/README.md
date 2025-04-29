# RTASPI dla Programistów Juniorów

## Scenariusz: Prosty system monitoringu z detekcją ruchu

Jako początkujący programista, chcesz stworzyć prosty system monitoringu, który:
1. Automatycznie wykryje kamerę internetową
2. Zastosuje detekcję ruchu
3. Zapisze wideo tylko wtedy, gdy wykryto ruch
4. Udostępni podgląd przez przeglądarkę

## Przewaga nad rozwiązaniami komercyjnymi

Komercyjne rozwiązania jak Nest Cam, Ring czy Arlo:
- Wymagają miesięcznych subskrypcji za zaawansowane funkcje
- Są zamknięte i niedostosowywalne
- Przechowują dane w chmurze, co rodzi obawy o prywatność

Z RTASPI tworzysz własne rozwiązanie:
- Bez kosztów subskrypcji
- Z pełną kontrolą nad danymi
- Z możliwością dostosowania do swoich potrzeb

## Kod rozwiązania

```python
# motion_detection_monitor.py
from rtaspi.core import rtaspi
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.constants import FilterType
import time
import os

# Inicjalizacja RTASPI z prostą konfiguracją
app = rtaspi()

# Automatyczne wykrywanie lokalnych urządzeń wideo
local_manager = LocalDevicesManager(app.config, app.mcp_broker)
local_manager.start()

# Poczekaj na wykrycie urządzeń
time.sleep(2)

# Pobierz pierwszą dostępną kamerę
video_devices = local_manager.get_devices_by_type("video")
if not video_devices:
    print("Nie znaleziono kamery. Podłącz kamerę i uruchom ponownie.")
    exit()

camera = next(iter(video_devices.values()))
print(f"Znaleziono kamerę: {camera.name}")

# Ustaw katalog do przechowywania nagrań
recordings_dir = "monitoring_recordings"
os.makedirs(recordings_dir, exist_ok=True)

# Utwórz pipeline z detekcją ruchu
motion_params = {
    "sensitivity": 0.6,  # Czułość detekcji (0.0-1.0)
    "min_area": 500,     # Minimalny obszar ruchu (w pikselach)
    "history": 50        # Historia tła
}

pipeline_config = {
    "input": {"device_id": camera.device_id},
    "stages": [
        {"type": "motion_detector", "params": motion_params}
    ],
    "output": [
        {
            "type": "record",
            "when_motion": True,  # Nagrywaj tylko gdy wykryto ruch
            "pre_buffer": 3,      # Zachowaj 3 sekundy przed wykryciem ruchu
            "post_buffer": 5,      # Kontynuuj nagrywanie 5 sekund po ustaniu ruchu
            "path": recordings_dir
        },
        {
            "type": "rtsp",     # Udostępnij jako strumień RTSP
            "path": "/live/camera"
        },
        {
            "type": "web",      # Udostępnij przez przeglądarkę
            "path": "/monitor"
        }
    ]
}

# Utwórz i uruchom pipeline
pipeline_id = app.create_pipeline(pipeline_config)
print(f"Uruchomiono pipeline detekcji ruchu z ID: {pipeline_id}")
print(f"Podgląd dostępny na: http://localhost:8081/monitor")
print(f"Strumień RTSP: rtsp://localhost:8554/live/camera")
print(f"Nagrania będą zapisywane w katalogu: {recordings_dir}")

# Główna pętla aplikacji
try:
    print("System monitoringu działa. Naciśnij Ctrl+C, aby zakończyć.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Zatrzymywanie systemu monitoringu...")
    app.stop()
```

## Jak uruchomić system

```bash
# Instalacja RTASPI przez pip
pip install rtaspi

# Uruchomienie systemu monitoringu
python motion_detection_monitor.py
```

## Co się dzieje w kodzie?

1. **Automatyczne wykrywanie kamery** - RTASPI wykrywa podłączoną kamerę bez konieczności ręcznej konfiguracji
2. **Konfiguracja detekcji ruchu** - Prosty słownik definiuje parametry detekcji ruchu
3. **Inteligentne nagrywanie** - System nagrywa tylko gdy wykryto ruch, oszczędzając miejsce na dysku
4. **Wielokanałowe wyjście** - Jednocześnie zapisuje nagrania i udostępnia podgląd przez RTSP i przeglądarkę
5. **Buforowanie przed i po zdarzeniu** - Zachowuje 3 sekundy przed i 5 sekund po detekcji ruchu

## Rozszerzenie funkcjonalności

Możesz łatwo rozszerzyć ten podstawowy system o dodatkowe funkcje:

```python
# Dodaj powiadomienia e-mail
pipeline_config["output"].append({
    "type": "email",
    "when_motion": True,
    "to": "twoj.email@example.com",
    "subject": "Wykryto ruch!",
    "with_snapshot": True  # Załącz zdjęcie
})

# Dodaj filtry poprawiające jakość obrazu
pipeline_config["stages"].insert(0, {
    "type": "image_enhancement",
    "params": {
        "brightness": 1.1,
        "contrast": 1.2
    }
})

# Dodaj prostą klasyfikację obiektów
pipeline_config["stages"].append({
    "type": "object_detector",
    "model": "tiny_yolo",  # Lekki model dla początkujących
    "classes": ["person", "car", "animal"],
    "confidence": 0.5
})
```

Ten przykład pokazuje, jak RTASPI umożliwia początkującym programistom tworzenie zaawansowanych systemów przetwarzania wideo przy minimalnej ilości kodu i wiedzy technicznej.