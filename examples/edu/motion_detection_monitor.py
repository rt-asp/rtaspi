#!/usr/bin/env python3

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
