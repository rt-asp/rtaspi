from rtaspi.core.mqtt import MQTTClient
import os
import json
from datetime import datetime

# Konfiguracja MQTT
mqtt_config = {
    "broker": "localhost",  # Adres brokera MQTT
    "port": 1883,
    "username": os.environ.get("MQTT_USERNAME", ""),
    "password": os.environ.get("MQTT_PASSWORD", ""),
    "client_id": "rtaspi_doorbell",
    "topics": {
        "events": "rtaspi/doorbell/events",
        "status": "rtaspi/doorbell/status",
        "command": "rtaspi/doorbell/command",
        "config": "rtaspi/doorbell/config"
    }
}

class DoorbellMQTTIntegration:
    def __init__(self, doorbell_app):
        self.doorbell = doorbell_app
        self.mqtt_client = MQTTClient(mqtt_config)
        self.setup_handlers()
        
    def setup_handlers(self):
        """Konfiguruje handlery dla różnych komend MQTT"""
        self.mqtt_client.subscribe(mqtt_config["topics"]["command"], self.handle_command)
        self.mqtt_client.subscribe(mqtt_config["topics"]["config"], self.handle_config)
        
    def handle_command(self, client, userdata, message):
        """Obsługuje komendy otrzymane przez MQTT"""
        try:
            command = json.loads(message.payload.decode())
            action = command.get("action")
            
            if action == "take_snapshot":
                self._handle_take_snapshot()
            elif action == "toggle_recording":
                self._handle_toggle_recording(command.get("enabled", True))
            elif action == "set_detection_sensitivity":
                self._handle_set_sensitivity(command.get("value", 0.6))
            elif action == "restart":
                self._handle_restart()
                
        except json.JSONDecodeError:
            print("Błąd: Nieprawidłowy format JSON w komendzie MQTT")
        except Exception as e:
            print(f"Błąd podczas przetwarzania komendy MQTT: {str(e)}")
            
    def handle_config(self, client, userdata, message):
        """Obsługuje aktualizacje konfiguracji przez MQTT"""
        try:
            config = json.loads(message.payload.decode())
            
            # Aktualizuj konfigurację detektora ruchu
            if "motion_detection" in config:
                motion_config = config["motion_detection"]
                self.doorbell.update_motion_config(
                    sensitivity=motion_config.get("sensitivity", 0.6),
                    min_area=motion_config.get("min_area", 500),
                    blur_size=motion_config.get("blur_size", 21)
                )
                
            # Aktualizuj konfigurację powiadomień
            if "notifications" in config:
                notif_config = config["notifications"]
                self.doorbell.update_notification_config(
                    enabled=notif_config.get("enabled", True),
                    quiet_hours_start=notif_config.get("quiet_hours_start", "22:00"),
                    quiet_hours_end=notif_config.get("quiet_hours_end", "07:00")
                )
                
        except json.JSONDecodeError:
            print("Błąd: Nieprawidłowy format JSON w konfiguracji MQTT")
        except Exception as e:
            print(f"Błąd podczas aktualizacji konfiguracji: {str(e)}")
            
    def _handle_take_snapshot(self):
        """Obsługuje żądanie wykonania zdjęcia"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.doorbell.RECORDINGS_DIR / f"mqtt_snapshot_{timestamp}.jpg"
        
        # Wykonaj zdjęcie
        self.doorbell.app.take_snapshot(
            self.doorbell.camera.device_id, 
            str(snapshot_path)
        )
        
        # Opublikuj informację o wykonanym zdjęciu
        self.mqtt_client.publish(
            mqtt_config["topics"]["events"],
            json.dumps({
                "event": "snapshot_taken",
                "path": str(snapshot_path),
                "timestamp": timestamp
            })
        )
        
    def _handle_toggle_recording(self, enabled):
        """Obsługuje włączanie/wyłączanie nagrywania"""
        if enabled:
            self.doorbell.start_recording()
        else:
            self.doorbell.stop_recording()
            
        self.mqtt_client.publish(
            mqtt_config["topics"]["status"],
            json.dumps({
                "recording": enabled,
                "timestamp": datetime.now().isoformat()
            })
        )
        
    def _handle_set_sensitivity(self, value):
        """Aktualizuje czułość detekcji ruchu"""
        self.doorbell.update_motion_config(sensitivity=value)
        
        self.mqtt_client.publish(
            mqtt_config["topics"]["status"],
            json.dumps({
                "motion_sensitivity": value,
                "timestamp": datetime.now().isoformat()
            })
        )
        
    def _handle_restart(self):
        """Restartuje system dzwonka"""
        self.mqtt_client.publish(
            mqtt_config["topics"]["status"],
            json.dumps({
                "status": "restarting",
                "timestamp": datetime.now().isoformat()
            })
        )
        
        self.doorbell.stop()
        self.doorbell.start()
        
        self.mqtt_client.publish(
            mqtt_config["topics"]["status"],
            json.dumps({
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
        )
        
    def publish_event(self, event_type, data=None):
        """Publikuje zdarzenie przez MQTT"""
        event_data = {
            "event": event_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            event_data.update(data)
            
        self.mqtt_client.publish(
            mqtt_config["topics"]["events"],
            json.dumps(event_data)
        )
        
    def start(self):
        """Uruchamia integrację MQTT"""
        self.mqtt_client.connect()
        
        # Opublikuj informację o uruchomieniu
        self.publish_event("startup", {
            "ip": self.doorbell._get_local_ip(),
            "web_interface": f"http://{self.doorbell._get_local_ip()}:8080/monitor",
            "webrtc_stream": f"webrtc://{self.doorbell._get_local_ip()}:8081/doorbell"
        })
        
    def stop(self):
        """Zatrzymuje integrację MQTT"""
        self.publish_event("shutdown")
        self.mqtt_client.disconnect()
