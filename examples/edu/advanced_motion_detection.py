#!/usr/bin/env python3

"""
Zaawansowany przykład systemu monitoringu z:
1. Detekcją ruchu
2. Powiadomieniami email
3. Detekcją obiektów
4. Poprawą jakości obrazu
"""

from rtaspi.core import rtaspi
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.constants import FilterType
import time
import os

def main():
    # Inicjalizacja RTASPI
    app = rtaspi()

    # Wykrywanie kamery
    local_manager = LocalDevicesManager(app.config, app.mcp_broker)
    local_manager.start()
    time.sleep(2)

    # Pobierz pierwszą dostępną kamerę
    video_devices = local_manager.get_devices_by_type("video")
    if not video_devices:
        print("Nie znaleziono kamery. Podłącz kamerę i uruchom ponownie.")
        return

    camera = next(iter(video_devices.values()))
    print(f"Znaleziono kamerę: {camera.name}")

    # Katalog na nagrania
    recordings_dir = "monitoring_recordings"
    os.makedirs(recordings_dir, exist_ok=True)

    # Konfiguracja zaawansowanego pipeline'u
    pipeline_config = {
        "input": {"device_id": camera.device_id},
        "stages": [
            # Poprawa jakości obrazu
            {
                "type": "image_enhancement",
                "params": {
                    "brightness": 1.1,
                    "contrast": 1.2,
                    "sharpness": 1.1
                }
            },
            # Detekcja ruchu
            {
                "type": "motion_detector",
                "params": {
                    "sensitivity": 0.6,
                    "min_area": 500,
                    "history": 50
                }
            },
            # Detekcja obiektów
            {
                "type": "object_detector",
                "model": "tiny_yolo",
                "classes": ["person", "car", "animal"],
                "confidence": 0.5
            }
        ],
        "output": [
            # Nagrywanie z detekcją ruchu
            {
                "type": "record",
                "when_motion": True,
                "pre_buffer": 3,
                "post_buffer": 5,
                "path": recordings_dir,
                "filename_pattern": "%Y%m%d_%H%M%S_{event_type}.mp4"
            },
            # Powiadomienia email
            {
                "type": "email",
                "when_motion": True,
                "to": "twoj.email@example.com",
                "subject": "Wykryto ruch!",
                "with_snapshot": True,
                "template": """
                Wykryto ruch w kamerze {camera_name}!
                
                Czas: {timestamp}
                Wykryte obiekty: {detected_objects}
                
                Załączono zdjęcie z momentu detekcji.
                """
            },
            # Podgląd przez przeglądarkę
            {
                "type": "web",
                "path": "/monitor",
                "with_controls": True,  # Dodaj kontrolki do podglądu
                "overlay": {
                    "motion": True,      # Pokaż obszary ruchu
                    "objects": True      # Pokaż wykryte obiekty
                }
            },
            # Strumień RTSP
            {
                "type": "rtsp",
                "path": "/live/camera"
            }
        ]
    }

    # Uruchom pipeline
    pipeline_id = app.create_pipeline(pipeline_config)
    print(f"\nUruchomiono zaawansowany system monitoringu!")
    print(f"ID pipeline'u: {pipeline_id}")
    print(f"\nDostęp do systemu:")
    print(f"- Podgląd WWW: http://localhost:8081/monitor")
    print(f"- Strumień RTSP: rtsp://localhost:8554/live/camera")
    print(f"- Nagrania: {recordings_dir}")
    print("\nFunkcje systemu:")
    print("- Detekcja ruchu z automatycznym nagrywaniem")
    print("- Powiadomienia email ze zdjęciami")
    print("- Detekcja obiektów (osoby, samochody, zwierzęta)")
    print("- Poprawa jakości obrazu")
    print("\nNaciśnij Ctrl+C aby zakończyć.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie systemu monitoringu...")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
