# Automation Examples

This directory contains examples demonstrating RTASPI's automation and integration capabilities.

## Examples

### 1. Rule-Based Automation (`rules_example.py`)
Shows how to:
- Define automation rules
- Create triggers and conditions
- Configure actions
- Handle events

### 2. MQTT Integration (`mqtt_example.py`)
Demonstrates:
- MQTT broker connection
- Topic subscription
- Message handling
- Device control

### 3. Home Assistant (`home_assistant.py`)
Features:
- Device discovery
- State synchronization
- Service integration
- Event handling

### 4. Scheduled Tasks (`scheduled_tasks.py`)
Implements:
- Time-based triggers
- Recurring tasks
- Conditional execution
- Task management

## Configuration Files

### `rules_config.yaml`
```yaml
rules:
  - name: motion_alert
    trigger:
      type: motion_detected
      device: camera1
      sensitivity: 0.8
    condition:
      time_range: [18:00, 06:00]
      days: [mon, tue, wed, thu, fri]
    action:
      - type: notification
        method: email
        recipient: security@example.com
      - type: recording
        duration: 30
        format: mp4

  - name: temperature_control
    trigger:
      type: temperature_change
      device: sensor1
      threshold: 25
    action:
      - type: device_control
        device: ac_unit
        command: power_on
```

### `mqtt_config.yaml`
```yaml
broker:
  host: localhost
  port: 1883
  username: ${MQTT_USER}
  password: ${MQTT_PASS}

topics:
  subscribe:
    - home/sensors/#
    - home/cameras/#
  publish:
    - home/controls/#
    - home/status/#

qos: 1
retain: true
```

## Requirements

- RTASPI with automation extensions
- MQTT broker (e.g., Mosquitto)
- Home Assistant instance
- Additional integration packages

## Usage

1. Configure automation:
```bash
# Copy and edit configuration
cp rules_config.yaml.example rules_config.yaml
cp mqtt_config.yaml.example mqtt_config.yaml
```

2. Run examples:
```bash
# Rule-based automation
python rules_example.py --config rules_config.yaml

# MQTT integration
python mqtt_example.py --config mqtt_config.yaml

# Home Assistant
python home_assistant.py --host http://homeassistant.local

# Scheduled tasks
python scheduled_tasks.py --schedule schedule.yaml
```

## Features

### Rule Engine
- Event-based triggers
- Time-based triggers
- Conditional logic
- Action chains

### MQTT Support
- Broker connection
- Topic management
- QoS levels
- Retained messages

### Home Assistant
- Device discovery
- State management
- Service calls
- Event subscription

### Scheduling
- Cron expressions
- Interval tasks
- One-time tasks
- Task dependencies

## Best Practices

1. Rule Design
   - Keep rules simple
   - Use clear naming
   - Document conditions
   - Test thoroughly

2. Integration
   - Handle disconnects
   - Validate messages
   - Manage resources
   - Log activities

3. Security
   - Use encryption
   - Validate inputs
   - Manage credentials
   - Monitor access

## Troubleshooting

Common issues and solutions:

1. Connection Issues
   - Check network
   - Verify credentials
   - Test connectivity
   - Check logs

2. Rule Problems
   - Validate syntax
   - Check conditions
   - Test triggers
   - Monitor execution

3. Integration
   - Verify compatibility
   - Check versions
   - Test endpoints
   - Monitor events

## Support

For automation-related issues:
- Check documentation
- Join automation channel on Discord
- Submit detailed bug reports
- Share rule configurations
