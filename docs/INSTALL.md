
## Uruchomienie

1. Uruchom główny skrypt:
```bash
python main.py
```

2. Opcjonalnie, możesz podać ścieżkę do pliku konfiguracyjnego:
```bash
python main.py -c /sciezka/do/config.yaml
```

## Protokół komunikacyjny MCP

System używa wewnętrznego protokołu komunikacyjnego MCP (Module Communication Protocol) do wymiany informacji między modułami. Protokół opiera się na wzorcu publikuj/subskrybuj (pub/sub), gdzie moduły mogą publikować wiadomości na określone tematy i subskrybować tematy, aby otrzymywać wiadomości.

### Przykładowe tematy MCP:

- `local_devices/devices` - Informacje o wykrytych lokalnych urządzeniach
- `local_devices/stream/started` - Informacja o uruchomieniu strumienia z lokalnego urządzenia
- `network_devices/devices` - Informacje o wykrytych urządzeniach sieciowych
- `command/local_devices/scan` - Komenda do skanowania lokalnych urządzeń
- `command/network_devices/add_device` - Komenda do dodania zdalnego urządzenia

## Używanie API

System udostępnia API do zarządzania urządzeniami i strumieniami. Poniżej znajdują się przykłady użycia API w kodzie Python:

```python
from core.mcp import MCPBroker, MCPClient

# Utwórz klienta MCP
broker = MCPBroker()
client = MCPClient(broker, client_id="my_client")

# Subskrybuj tematy
client.subscribe("local_devices/devices", handler=handle_devices)
client.subscribe("local_devices/stream/started", handler=handle_stream_started)

# Wysyłaj komendy
client.publish("command/local_devices/scan", {})

# Uruchom strumień z urządzenia
client.publish("command/local_devices/start_stream", {
    "device_id": "video:/dev/video0",
    "protocol": "rtsp"
})

# Dodaj zdalne urządzenie
client.publish("command/network_devices/add_device", {
    "name": "Kamera IP",
    "ip": "192.168.1.100",
    "port": 554,
    "username": "admin",
    "password": "admin",
    "type": "video",
    "protocol": "rtsp",
    "paths": ["cam/realmonitor"]
})
```

## Testy

Uruchomienie testów jednostkowych:
```bash
pytest -v tests/
```

## Licencja

Ten projekt jest udostępniany na licencji Apache 2. Zobacz plik LICENSE, aby uzyskać więcej informacji.

## Autorzy

- Zespół rtaspi

## Współpraca

Zachęcamy do współpracy przy rozwoju projektu. Zapraszamy do zgłaszania problemów (issues) i propozycji zmian (pull requests).