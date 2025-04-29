# Speech Processing Examples

This directory contains examples demonstrating RTASPI's speech processing capabilities.

## Examples

### 1. Speech Recognition (`speech_recognition.py`)
Shows how to:
- Capture audio input
- Perform real-time transcription
- Handle multiple languages
- Process commands

### 2. Text-to-Speech (`text_to_speech.py`)
Demonstrates:
- Voice synthesis
- Language selection
- Voice customization
- Audio output control

### 3. Real-time Translation (`realtime_translation.py`)
Features:
- Speech-to-speech translation
- Multiple language support
- Real-time processing
- Audio streaming

### 4. Voice Assistant (`voice_assistant.py`)
Implements:
- Command recognition
- Natural language processing
- Custom actions
- Response generation

## Configuration Files

### `speech_config.yaml`
```yaml
recognition:
  engine: whisper
  model: medium
  language: auto
  device: cuda

synthesis:
  engine: pyttsx3
  voice: english
  rate: 150
  volume: 1.0

translation:
  source_lang: en
  target_lang: es
  api_key: ${TRANSLATION_API_KEY}
```

### `commands_config.yaml`
```yaml
commands:
  - name: turn_on_lights
    phrases:
      - "turn on the lights"
      - "lights on"
    action: home_automation.lights.on
    
  - name: start_recording
    phrases:
      - "start recording"
      - "begin capture"
    action: camera.start_recording
```

## Requirements

- RTASPI with speech extensions
- OpenAI Whisper
- PyTTSx3
- Additional language models

## Usage

1. Configure speech features:
```bash
# Copy and edit configuration
cp speech_config.yaml.example speech_config.yaml
cp commands_config.yaml.example commands_config.yaml
```

2. Run examples:
```bash
# Speech recognition
python speech_recognition.py --config speech_config.yaml

# Text-to-speech
python text_to_speech.py --text "Hello World"

# Real-time translation
python realtime_translation.py --source en --target es

# Voice assistant
python voice_assistant.py --commands commands_config.yaml
```

## Features

### Speech Recognition
- Multiple engine support
  - OpenAI Whisper
  - Mozilla DeepSpeech
  - Google Speech API
- Real-time processing
- Noise reduction
- Speaker diarization

### Text-to-Speech
- Multiple voices
- Speed control
- Pitch adjustment
- SSML support

### Translation
- 50+ languages
- Real-time capability
- Accent preservation
- Custom vocabulary

### Voice Assistant
- Custom commands
- Context awareness
- Action triggers
- Conversation flow

## Model Management

### Local Models
- Download management
- Version control
- Cache handling
- Performance optimization

### Cloud Services
- API integration
- Fallback handling
- Rate limiting
- Cost management

## Best Practices

1. Audio Input
   - Use quality microphones
   - Proper noise isolation
   - Correct sampling rate
   - Buffer management

2. Processing
   - GPU acceleration
   - Batch processing
   - Stream management
   - Error handling

3. Output
   - Audio device selection
   - Latency management
   - Quality control
   - Format handling

## Troubleshooting

Common issues and solutions:

1. Recognition Problems
   - Check audio input
   - Verify model compatibility
   - Adjust sensitivity
   - Update models

2. Performance Issues
   - Enable GPU acceleration
   - Optimize model size
   - Adjust buffer sizes
   - Check resource usage

3. Integration
   - Verify API keys
   - Check network connection
   - Test endpoints
   - Monitor quotas

## Support

For speech-related issues:
- Check documentation
- Join speech processing channel on Discord
- Submit detailed bug reports
- Share model improvements
