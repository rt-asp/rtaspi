#!/usr/bin/env python3

"""
Prosty przykład strumieniowania obrazu z kamery.
Ten przykład pokazuje podstawowe użycie RTASPI do:
1. Wykrycia kamery
2. Utworzenia prostego pipeline'u
3. Udostępnienia podglądu przez przeglądarkę
"""

from rtaspi.core import rtaspi
from rtaspi.device_managers.local_devices import LocalDevicesManager
import time

def main():
    # Inicjalizacja RTASPI
    app = rtaspi()

    # Utworzenie menedżera urządzeń lokalnych
    local_manager = LocalDevicesManager(app.config, app.mcp_broker)
    local_manager.start()

    # Krótkie opóźnienie na wykrycie urządzeń
    print("Wykrywanie urządzeń wideo...")
    time.sleep(2)

    # Pobierz listę urządzeń wideo
    video_devices = local_manager.get_devices_by_type("video")
    
    if not video_devices:
        print("Nie znaleziono żadnej kamery!")
        return
    
    # Użyj pierwszej dostępnej kamery
    camera = next(iter(video_devices.values()))
    print(f"Znaleziono kamerę: {camera.name}")

    # Konfiguracja prostego pipeline'u
    pipeline_config = {
        "input": {
            "device_id": camera.device_id
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
    pipeline_id = app.create_pipeline(pipeline_config)
    print(f"Pipeline utworzony z ID: {pipeline_id}")
    print(f"Podgląd dostępny na: http://localhost:8081/camera")

    try:
        print("\nStrumień jest aktywny. Naciśnij Ctrl+C aby zakończyć.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie strumienia...")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
