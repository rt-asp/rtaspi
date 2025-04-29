#!/usr/bin/env python3

"""
Przykłady różnych konfiguracji pipeline'ów w RTASPI.
Ten plik pokazuje różne możliwości konfiguracji przetwarzania
i strumieniowania wideo z wykorzystaniem pipeline'ów.
"""

from rtaspi.core import rtaspi
from rtaspi.device_managers.local_devices import LocalDevicesManager
import time
import os

def get_camera():
    """Pomocnicza funkcja do pobierania pierwszej dostępnej kamery"""
    app = rtaspi()
    local_manager = LocalDevicesManager(app.config, app.mcp_broker)
    local_manager.start()
    time.sleep(2)
    
    video_devices = local_manager.get_devices_by_type("video")
    if not video_devices:
        return None, None
    
    camera = next(iter(video_devices.values()))
    return app, camera

def przykład_1_podstawowy():
    """Podstawowy pipeline z jednym wyjściem web"""
    app, camera = get_camera()
    if not camera:
        print("Nie znaleziono kamery!")
        return

    config = {
        "input": {"device_id": camera.device_id},
        "output": [
            {"type": "web", "path": "/kamera"}
        ]
    }
    
    return app.create_pipeline(config)

def przykład_2_filtry_obrazu():
    """Pipeline z filtrami poprawiającymi jakość obrazu"""
    app, camera = get_camera()
    if not camera:
        print("Nie znaleziono kamery!")
        return

    config = {
        "input": {"device_id": camera.device_id},
        "stages": [
            {
                "type": "image_enhancement",
                "params": {
                    "brightness": 1.2,
                    "contrast": 1.1,
                    "saturation": 1.1,
                    "sharpness": 1.2
                }
            },
            {
                "type": "noise_reduction",
                "params": {
                    "strength": 0.3
                }
            }
        ],
        "output": [
            {"type": "web", "path": "/kamera-hd"}
        ]
    }
    
    return app.create_pipeline(config)

def przykład_3_multi_output():
    """Pipeline z wieloma wyjściami"""
    app, camera = get_camera()
    if not camera:
        print("Nie znaleziono kamery!")
        return

    config = {
        "input": {"device_id": camera.device_id},
        "output": [
            {"type": "web", "path": "/kamera"},
            {"type": "rtsp", "path": "/live"},
            {
                "type": "record",
                "path": "nagrania",
                "filename_pattern": "%Y%m%d_%H%M%S.mp4",
                "segment_time": 300  # Nowy plik co 5 minut
            }
        ]
    }
    
    return app.create_pipeline(config)

def przykład_4_detekcja_i_analiza():
    """Pipeline z detekcją obiektów i analizą ruchu"""
    app, camera = get_camera()
    if not camera:
        print("Nie znaleziono kamery!")
        return

    config = {
        "input": {"device_id": camera.device_id},
        "stages": [
            {
                "type": "motion_detector",
                "params": {
                    "sensitivity": 0.7,
                    "min_area": 300
                }
            },
            {
                "type": "object_detector",
                "model": "tiny_yolo",
                "classes": ["person", "car"],
                "confidence": 0.5
            }
        ],
        "output": [
            {
                "type": "web",
                "path": "/analiza",
                "overlay": {
                    "motion": True,
                    "objects": True,
                    "statistics": True
                }
            }
        ]
    }
    
    return app.create_pipeline(config)

def przykład_5_adaptacyjny():
    """Pipeline z adaptacyjnymi parametrami"""
    app, camera = get_camera()
    if not camera:
        print("Nie znaleziono kamery!")
        return

    config = {
        "input": {"device_id": camera.device_id},
        "stages": [
            {
                "type": "adaptive_enhancement",
                "params": {
                    "target_brightness": 0.5,
                    "min_contrast": 1.0,
                    "max_contrast": 1.5
                }
            }
        ],
        "output": [
            {"type": "web", "path": "/adaptacyjny"}
        ]
    }
    
    return app.create_pipeline(config)

def main():
    print("Demonstracja różnych konfiguracji pipeline'ów RTASPI\n")

    # Przykład 1
    print("1. Uruchamianie podstawowego pipeline'a...")
    pipeline1_id = przykład_1_podstawowy()
    if pipeline1_id:
        print(f"   Pipeline podstawowy dostępny na: http://localhost:8081/kamera")

    # Przykład 2
    print("\n2. Uruchamianie pipeline'a z filtrami obrazu...")
    pipeline2_id = przykład_2_filtry_obrazu()
    if pipeline2_id:
        print(f"   Pipeline z ulepszoną jakością dostępny na: http://localhost:8081/kamera-hd")

    # Przykład 3
    print("\n3. Uruchamianie pipeline'a z wieloma wyjściami...")
    pipeline3_id = przykład_3_multi_output()
    if pipeline3_id:
        print(f"   - Web: http://localhost:8081/kamera")
        print(f"   - RTSP: rtsp://localhost:8554/live")
        print(f"   - Nagrania zapisywane w katalogu: nagrania/")

    # Przykład 4
    print("\n4. Uruchamianie pipeline'a z detekcją i analizą...")
    pipeline4_id = przykład_4_detekcja_i_analiza()
    if pipeline4_id:
        print(f"   Pipeline analityczny dostępny na: http://localhost:8081/analiza")

    # Przykład 5
    print("\n5. Uruchamianie pipeline'a adaptacyjnego...")
    pipeline5_id = przykład_5_adaptacyjny()
    if pipeline5_id:
        print(f"   Pipeline adaptacyjny dostępny na: http://localhost:8081/adaptacyjny")

    print("\nWszystkie pipeline'y uruchomione. Naciśnij Ctrl+C aby zakończyć.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie wszystkich pipeline'ów...")

if __name__ == "__main__":
    main()
