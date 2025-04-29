# RTASPI dla Entuzjastów IoT

## Scenariusz: Inteligentny dzwonek do drzwi z Raspberry Pi

Jako entuzjasta IoT, chcesz stworzyć własny inteligentny dzwonek do drzwi używając Raspberry Pi, który:
1. Wykrywa osoby przed drzwiami
2. Wysyła powiadomienie na telefon
3. Nagrywa wideo z wizyty
4. Umożliwia podgląd na żywo i komunikację dwukierunkową

## Przewaga nad rozwiązaniami komercyjnymi

Komercyjne rozwiązania jak Ring Doorbell czy Nest Doorbell:
- Wymagają regularnych opłat abonamentowych (ok. 30-60 zł miesięcznie)
- Mają ograniczone możliwości integracji z innymi systemami
- Przechowują nagrania w chmurze producenta
- Mogą gromadzić dane o użytkownikach

Z RTASPI budujesz własne rozwiązanie:
- Jednorazowy koszt sprzętu (Raspberry Pi + kamera) ok. 200-300 zł
- Brak opłat abonamentowych
- Pełna kontrola nad danymi i prywatnością
- Nieograniczone możliwości integracji z innymi systemami smart home

## Potrzebny sprzęt

- Raspberry Pi (3B+, 4 lub nowszy)
- Kamera kompatybilna z Raspberry Pi (np. Camera Module V2)
- Głośnik/buzzer (np. MAX98357A I2S)
- Mikrofon (np. USB lub I2S MEMS)
- Przycisk dzwonka
- Opcjonalnie: czujnik ruchu PIR
- Obudowa odporna na warunki atmosferyczne

## Kod rozwiązania

### 1. Instalacja RTASPI na Raspberry Pi

```bash
# Zaktualizuj system
sudo apt update && sudo apt upgrade -y

# Zainstaluj wymagane zależności
sudo apt install -y python3-pip ffmpeg libopencv-dev portaudio19-dev

# Zainstaluj RTASPI
pip3 install rtaspi

# Utwórz katalog na nagrania
mkdir -p ~/doorbell/recordings
```

### 2. Konfiguracja systemu dzwonka

Utwórz plik `smart_doorbell.py`:

```python
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
```

### 3. Konfiguracja aplikacji mobilnej

Dla pełnego rozwiązania potrzebujesz prostej aplikacji mobilnej do odbierania powiadomień i wyświetlania podglądu kamery. RTASPI oferuje gotowe komponenty React Native do integracji:

```javascript
// Przykład komponentu React Native dla integracji z RTASPI
import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image, StyleSheet } from 'react-native';
import { RTASPIWebRTC } from 'rtaspi-react-native';

const DoorbellApp = () => {
  const [connected, setConnected] = useState(false);
  const [lastImage, setLastImage] = useState(null);
  const [doorbellIP, setDoorbellIP] = useState('192.168.1.100'); // Adres IP twojego Raspberry Pi
  
  // Połącz z dzwonkiem
  const connectToDoorbell = () => {
    setConnected(true);
  };
  
  // Rozłącz z dzwonkiem
  const disconnectFromDoorbell = () => {
    setConnected(false);
  };
  
  // Odpowiedz na dzwonek
  const answerDoorbell = () => {
    // Kod do nawiązania dwukierunkowej komunikacji audio
    console.log('Odpowiadanie na dzwonek...');
  };
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Inteligentny Dzwonek</Text>
      
      {connected ? (
        <>
          <RTASPIWebRTC 
            serverUrl={`webrtc://${doorbellIP}:8081/doorbell`}
            style={styles.videoStream}
          />
          <Button title="Rozłącz" onPress={disconnectFromDoorbell} />
          <Button title="Odpowiedz" onPress={answerDoorbell} />
        </>
      ) : (
        <>
          {lastImage && (
            <Image source={{ uri: lastImage }} style={styles.lastImage} />
          )}
          <Button title="Połącz" onPress={connectToDoorbell} />
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
  },
  videoStream: {
    width: '100%',
    height: 300,
    marginBottom: 20,
    backgroundColor: '#000',
  },
  lastImage: {
    width: '100%',
    height: 200,
    marginBottom: 20,
    resizeMode: 'cover',
  },
});

export default DoorbellApp;
```

## Integracja z istniejącymi systemami Smart Home

### 1. Integracja z Home Assistant

```yaml
# configuration.yaml dla Home Assistant
rtaspi:
  host: 192.168.1.100
  port: 8080
  devices:
    - name: Doorbell Camera
      type: camera
      stream_url: rtsp://192.168.1.100:8554/doorbell
      snapshot_url: http://192.168.1.100:8080/api/snapshot/doorbell
      
automation:
  - alias: "Powiadomienie o dzwonku do drzwi"
    trigger:
      platform: mqtt
      topic: rtaspi/doorbell/events
      payload: 'button_pressed'
    action:
      - service: notify.mobile_app
        data:
          title: "Dzwonek do drzwi"
          message: "Ktoś dzwoni do drzwi"
          data:
            image: "{{ states.camera.doorbell_camera.attributes.entity_picture }}"
```

### 2. Integracja z MQTT

RTASPI można łatwo zintegrować z innymi systemami Smart Home poprzez MQTT. Dodaj poniższy kod do poprzedniego rozwiązania:

```python
from rtaspi.core.mqtt import MQTTClient

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
        "command": "rtaspi/doorbell/command"
    }
}

# Inicjalizacja klienta MQTT
mqtt_client = MQTTClient(mqtt_config)

# Funkcja obsługująca komendy przez MQTT
def handle_mqtt_command(client, userdata, message):
    command = message.payload.decode()
    if command == "take_snapshot":
        # Zrób zdjęcie i wyślij URL przez MQTT
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = RECORDINGS_DIR / f"mqtt_snapshot_{timestamp}.jpg"
        app.take_snapshot(self.camera.device_id, str(snapshot_path))
        mqtt_client.publish(mqtt_config["topics"]["events"], 
                           f"snapshot_taken:{str(snapshot_path)}")
    elif command == "toggle_recording":
        # Włącz/wyłącz ciągłe nagrywanie
        # Kod obsługi nagrywania...
        pass

# Dodaj subskrypcję tematu poleceń
mqtt_client.subscribe(mqtt_config["topics"]["command"], handle_mqtt_command)

# Dodaj do klasy SmartDoorbell
def _handle_doorbell_press(self):
    # [...istniejący kod...]
    
    # Publikuj zdarzenie przez MQTT
    mqtt_client.publish(mqtt_config["topics"]["events"], "button_pressed")
```

## Przewaga RTASPI nad komercyjnymi rozwiązaniami

### Porównanie z Ring Doorbell:

| Funkcja | Ring Doorbell | RTASPI Doorbell |
|---------|---------------|-----------------|
| Koszt sprzętu | Ok. 800-1200 zł | Ok. 200-300 zł (Raspberry Pi + akcesoria) |
| Opłaty miesięczne | 30-60 zł/miesiąc | Brak |
| Prywatność | Nagrania w chmurze Ring/Amazon | Pełna kontrola, dane lokalnie |
| Integracja | Ograniczona, zamknięty ekosystem | Nieograniczona, otwarty system |
| Powiadomienia | Tak | Tak |
| Detekcja osób | Tak, z planem płatnym | Tak, bez opłat |
| Dostosowanie | Ograniczone | Pełna swoboda modyfikacji |
| Nagrywanie | Limitowane lub z opłatami | Bez limitów |

### Przewaga rozwiązania RTASPI:

1. **Ekonomia** - Brak miesięcznych opłat za usługi chmurowe
2. **Prywatność** - Wszystkie dane i nagrania pozostają w twojej sieci lokalnej
3. **Kontrola** - Pełne zarządzanie funkcjami, algorytmami detekcji i przechowywaniem
4. **Integracja** - Łatwa integracja z istniejącymi systemami (Home Assistant, OpenHAB, itp.)
5. **Nauka** - Okazja do nauki programowania, elektroniki i systemów AI



