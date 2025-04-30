#!/usr/bin/env python3

"""
Zaawansowany przykład systemu monitoringu z:
1. Detekcją ruchu
2. Powiadomieniami email
3. Detekcją obiektów
4. Poprawą jakości obrazu
"""

from rtaspi.core.rtaspi import RTASPI
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.constants import FilterType
from rtaspi.constants.devices import DEVICE_TYPE_CAMERA, CAPABILITY_VIDEO
from rtaspi.constants.outputs import OutputType
from rtaspi.constants.protocols import ProtocolType
from rtaspi.constants.resolutions import Resolution
from rtaspi.constants.filters import (
    FILTER_BRIGHTNESS,
    FILTER_CONTRAST,
    FILTER_SHARPEN,
    FILTER_MOTION_DETECTION,
    FILTER_FACE_DETECTION
)
from rtaspi.core.defaults import DEFAULT_CONFIG
import time
import os

def main():
    # Inicjalizacja RTASPI
    app = RTASPI()

    # Pobierz pierwszą dostępną kamerę
    video_devices = app.devices.list(type=DEVICE_TYPE_CAMERA)
    if not video_devices:
        print("Nie znaleziono kamery. Podłącz kamerę i uruchom ponownie.")
        return

    camera = video_devices[0]
    print(f"Znaleziono kamerę: {camera['name']}")

    # Katalog na nagrania
    recordings_dir = "monitoring_recordings"
    os.makedirs(recordings_dir, exist_ok=True)

    # Konfiguracja zaawansowanego pipeline'u
    pipeline_config = {
        "input": {
            "device_id": camera['id'],
            "resolution": Resolution.HD.value
        },
        "stages": [
            # Poprawa jakości obrazu
            {
                "type": FilterType.COLOR_BALANCE.name.lower(),
                "filters": [
                    {
                        "type": FILTER_BRIGHTNESS,
                        "value": 1.1
                    },
                    {
                        "type": FILTER_CONTRAST,
                        "value": 1.2
                    },
                    {
                        "type": FILTER_SHARPEN,
                        "value": 1.1
                    }
                ]
            },
            # Detekcja ruchu
            {
                "type": FILTER_MOTION_DETECTION,
                "params": {
                    "sensitivity": 0.6,
                    "min_area": 500,
                    "history": 50
                }
            },
            # Detekcja obiektów
            {
                "type": FILTER_FACE_DETECTION,
                "model": "tiny_yolo",
                "classes": ["person", "car", "animal"],
                "confidence": 0.5
            }
        ],
        "output": [
            # Nagrywanie z detekcją ruchu
            {
                "type": OutputType.MP4_FILE.name.lower(),
                "when_motion": True,
                "pre_buffer": 3,
                "post_buffer": 5,
                "path": recordings_dir,
                "filename_pattern": "%Y%m%d_%H%M%S_{event_type}.mp4"
            },
            # Powiadomienia email
            {
                "type": OutputType.EVENT_HTTP.name.lower(),
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
                "type": OutputType.DISPLAY.name.lower(),
                "path": "/monitor",
                "with_controls": True,  # Dodaj kontrolki do podglądu
                "overlay": {
                    "motion": True,      # Pokaż obszary ruchu
                    "objects": True      # Pokaż wykryte obiekty
                }
            },
            # Strumień RTSP
            {
                "type": OutputType.RTSP.name.lower(),
                "path": "/live/camera",
                "protocol": ProtocolType.RTSP.name.lower()
            }
        ]
    }

    # Uruchom pipeline
    pipeline_id = app.pipelines.create(pipeline_config)
    app.pipelines.start(pipeline_id)
    print(f"\nUruchomiono zaawansowany system monitoringu!")
    print(f"ID pipeline'u: {pipeline_id}")
    print(f"\nDostęp do systemu:")
    print(f"- Podgląd WWW: {ProtocolType.HTTP.name.lower()}://{DEFAULT_CONFIG['web']['host']}:{DEFAULT_CONFIG['web']['port']}/monitor")
    print(f"- Strumień RTSP: {ProtocolType.RTSP.name.lower()}://{DEFAULT_CONFIG['web']['host']}:{DEFAULT_CONFIG['streaming']['rtsp']['port_start']}/live/camera")
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
        app.cleanup()

if __name__ == "__main__":
    main()
