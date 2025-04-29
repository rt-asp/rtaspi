#!/usr/bin/env python3
import time
import os
import threading
import RPi.GPIO as GPIO
from pathlib import Path
from datetime import datetime
from rtaspi.core import rtaspi
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.processing.notifications import NotificationManager

# Konfiguracja GPIO
BUTTON_PIN = 18
PIR_PIN = 23
LED_PIN = 24
BUZZER_PIN = 25

# Inicjalizacja GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Katalog na nagrania
RECORDINGS_DIR = Path.home() / "doorbell" / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Konfiguracja RTASPI
config = {
    "system": {
        "storage_path": str(RECORDINGS_DIR),
        "log_level": "INFO"
    },
    "web": {
        "enable": True,
        "port": 8080,
        "enable_https": False  # Zmień na True dla produkcji
    },
    "streaming": {
        "webrtc": {
            "port_start": 8081,
            "stun_server": "stun:stun.l.google.com:19302"
        }
    },
    "notifications": {
        "push": {
            "service": "pushover",  # Alternatywnie: "telegram", "email", "custom_webhook"
            "api_key": os.environ.get("PUSHOVER_API_KEY", ""),
            "user_key": os.environ.get("PUSHOVER_USER_KEY", "")
        }
    }
}

# Inicjalizacja RTASPI
app = rtaspi(config=config)

class SmartDoorbell:
    def __init__(self):
        self.app = app
        self.notification_manager = NotificationManager(app.config)
        self.running = False
        self.devices = {}
        self.pipeline_id = None
        self.person_detected = False
        self.last_detection_time = 0
        self.last_button_press = 0
        
    def start(self):
        """Uruchamia system dzwonka"""
        self.running = True
        
        # Wykryj urządzenia
        local_manager = LocalDevicesManager(app.config, app.mcp_broker)
        local_manager.start()
        time.sleep(2)  # Poczekaj na wykrycie urządzeń
        
        # Pobierz urządzenia
        self.devices = local_manager.get_devices_by_type("video")
        if not self.devices:
            print("Nie znaleziono kamery. Sprawdź połączenie.")
            return False
            
        # Pobierz pierwsze urządzenie wideo
        self.camera = next(iter(self.devices.values()))
        print(f"Znaleziono kamerę: {self.camera.name}")
        
        # Konfiguracja pipelineu
        pipeline_config = {
            "input": {"device_id": self.camera.device_id},
            "stages": [
                {
                    "type": "resize",
                    "params": {"width": 640, "height": 480}
                },
                {
                    "type": "face_detector",
                    "params": {
                        "model": "haarcascade",  # Lekki detektor twarzy
                        "scale_factor": 1.3,
                        "min_neighbors": 5
                    }
                },
                {
                    "type": "person_detector",
                    "params": {
                        "model": "mobilenet_ssd",  # Lekki model dla Raspberry Pi
                        "confidence": 0.6
                    }
                }
            ],
            "output": [
                {
                    "type": "record",
                    "when_detection": True,  # Nagrywaj tylko gdy wykryto osobę
                    "pre_buffer": 2,
                    "post_buffer": 10,
                    "format": "mp4",
                    "path": str(RECORDINGS_DIR)
                },
                {
                    "type": "webrtc",  # Strumieniowanie WebRTC do aplikacji mobilnej
                    "path": "/doorbell"
                },
                {
                    "type": "web",      # Interfejs Web dla podglądu
                    "path": "/monitor"
                }
            ]
        }
        
        # Utwórz i uruchom pipeline
        self.pipeline_id = app.create_pipeline(pipeline_config)
        print(f"Uruchomiono pipeline z ID: {self.pipeline_id}")
        
        # Uruchom wątki monitorujące
        threading.Thread(target=self._button_monitor, daemon=True).start()
        threading.Thread(target=self._pir_monitor, daemon=True).start()
        threading.Thread(target=self._detection_callback, daemon=True).start()
        
        return True
        
    def stop(self):
        """Zatrzymuje system dzwonka"""
        self.running = False
        if self.pipeline_id:
            app.stop_pipeline(self.pipeline_id)
        app.stop()
        GPIO.cleanup()
        
    def _button_monitor(self):
        """Monitoruje przycisk dzwonka"""
        while self.running:
            if not GPIO.input(BUTTON_PIN):  # Przycisk wciśnięty (aktywny niski)
                current_time = time.time()
                if current_time - self.last_button_press > 2:  # Debounce 2 sekundy
                    self.last_button_press = current_time
                    self._handle_doorbell_press()
            time.sleep(0.1)
            
    def _pir_monitor(self):
        """Monitoruje czujnik ruchu PIR"""
        while self.running:
            if GPIO.input(PIR_PIN):  # Wykryto ruch
                current_time = time.time()
                if current_time - self.last_detection_time > 30:  # Co najmniej 30s od ostatniej detekcji
                    self.last_detection_time = current_time
                    self._handle_motion_detected()
            time.sleep(0.5)
            
    def _handle_doorbell_press(self):
        """Obsługuje naciśnięcie przycisku dzwonka"""
        print("Dzwonek naciśnięty!")
        
        # Migaj diodą LED
        threading.Thread(target=self._blink_led, args=(5,), daemon=True).start()
        
        # Uruchom buzzer
        threading.Thread(target=self._buzzer_ring, daemon=True).start()
        
        # Zrób zdjęcie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = RECORDINGS_DIR / f"doorbell_press_{timestamp}.jpg"
        app.take_snapshot(self.camera.device_id, str(snapshot_path))
        
        # Wyślij powiadomienie
        self.notification_manager.send_notification(
            title="Dzwonek do drzwi!",
            message="Ktoś dzwoni do drzwi",
            image_path=str(snapshot_path),
            url=f"http://{self._get_local_ip()}:8080/monitor"
        )
        
    def _handle_motion_detected(self):
        """Obsługuje wykrycie ruchu przez PIR"""
        print("Wykryto ruch przez czujnik PIR")
        # Włącz diodę LED
        GPIO.output(LED_PIN, GPIO.HIGH)
        # Zapisz stan detekcji ruchu
        self.motion_detected = True
        # Wyłącz diodę po 5 sekundach
        threading.Timer(5, lambda: GPIO.output(LED_PIN, GPIO.LOW)).start()
        
    def _detection_callback(self):
        """Callback dla detekcji osób"""
        while self.running:
            # Sprawdź czy pipeline wykrył osobę
            detection_results = app.get_pipeline_results(self.pipeline_id)
            if detection_results and 'detections' in detection_results:
                has_person = any(d['class'] == 'person' and d['confidence'] > 0.7 
                                for d in detection_results['detections'])
                
                if has_person and not self.person_detected:
                    self.person_detected = True
                    self._handle_person_detected(detection_results)
                elif not has_person and self.person_detected:
                    self.person_detected = False
            
            time.sleep(1)
            
    def _handle_person_detected(self, detection_results):
        """Obsługuje wykrycie osoby"""
        print("Wykryto osobę!")
        current_time = time.time()
        
        # Ogranicz powiadomienia do jednego na 60 sekund
        if current_time - self.last_detection_time < 60:
            return
            
        self.last_detection_time = current_time
        
        # Zrób zdjęcie z zaznaczoną detekcją
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = RECORDINGS_DIR / f"person_detected_{timestamp}.jpg"
        app.take_snapshot(self.camera.device_id, str(snapshot_path), 
                         with_annotations=True)
        
        # Wyślij powiadomienie
        self.notification_manager.send_notification(
            title="Wykryto osobę!",
            message="Ktoś jest przy drzwiach",
            image_path=str(snapshot_path),
            url=f"http://{self._get_local_ip()}:8080/monitor"
        )
        
    def _blink_led(self, times=5):
        """Miga diodą LED"""
        for _ in range(times):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)
            
    def _buzzer_ring(self):
        """Uruchamia buzzer z melodią dzwonka"""
        # Prosta melodia dzwonka - dwa tony
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.4)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        
    def _get_local_ip(self):
        """Pobiera lokalny adres IP Raspberry Pi"""
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

# Uruchom system dzwonka
if __name__ == "__main__":
    doorbell = SmartDoorbell()
    
    if doorbell.start():
        print(f"System dzwonka uruchomiony!")
        print(f"Interfejs Web dostępny na: http://{doorbell._get_local_ip()}:8080/monitor")
        print(f"Strumień WebRTC: webrtc://{doorbell._get_local_ip()}:8081/doorbell")
        
        try:
            # Utrzymuj program działający
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Zatrzymywanie systemu dzwonka...")
        finally:
            doorbell.stop()
