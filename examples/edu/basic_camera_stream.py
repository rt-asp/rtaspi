#!/usr/bin/env python3

"""
Prosty przykład strumieniowania obrazu z kamery.
Ten przykład pokazuje podstawowe użycie RTASPI do:
1. Wykrycia kamery
2. Utworzenia prostego pipeline'u
3. Udostępnienia podglądu przez przeglądarkę
"""

from rtaspi.core.rtaspi import RTASPI
from rtaspi.device_managers.local_devices import LocalDevicesManager
import time

def main():
    # Inicjalizacja RTASPI
    app = RTASPI()

    # Wykrywanie urządzeń wideo
    print("Wykrywanie urządzeń wideo...")
    video_devices = app.devices.list(type="video")
    
    if not video_devices:
        print("Nie znaleziono żadnej kamery!")
        return
    
    # Użyj pierwszej dostępnej kamery
    camera = video_devices[0]
    print(f"Znaleziono kamerę: {camera['name']}")

    # Konfiguracja prostego pipeline'u
    pipeline_config = {
        "input": {
            "device_id": camera['id']
        },
        "stages": [
            # Możemy dodać filtry obrazu, np.:
            {
                "type": "image_enhancement",
                "params": {
                    "brightness": 1.1,
                    "contrast": 1.2
                }
            }
        ],
        "output": [
            {
                "type": "web",
                "path": "/camera"
            }
        ]
    }

    # Utworzenie i uruchomienie pipeline'u
    pipeline_id = app.pipelines.create(pipeline_config)
    app.pipelines.start(pipeline_id)
    print(f"Pipeline utworzony z ID: {pipeline_id}")
    print(f"Podgląd dostępny na: http://localhost:8081/camera")

    try:
        print("\nStrumień jest aktywny. Naciśnij Ctrl+C aby zakończyć.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie strumienia...")
    finally:
        app.cleanup()

if __name__ == "__main__":
    main()
