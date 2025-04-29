# Pipeline Processing Examples

This directory contains examples demonstrating RTASPI's pipeline processing capabilities.

## Examples

### 1. Face Detection (`face_detection.py`)
Shows how to:
- Detect faces in video streams
- Track facial features
- Apply face filters
- Generate analytics

### 2. Motion Detection (`motion_detection.py`)
Demonstrates:
- Movement tracking
- Zone monitoring
- Object persistence
- Alert generation

### 3. Object Tracking (`object_tracking.py`)
Features:
- Multi-object tracking
- Object classification
- Path prediction
- Collision detection

### 4. Audio Processing (`audio_processing.py`)
Implements:
- Noise reduction
- Audio filtering
- Feature extraction
- Sound classification

## Configuration Files

### `pipeline_config.yaml`
```yaml
input:
  source: camera0
  format: mjpeg
  resolution: 1920x1080
  fps: 30

processing:
  - name: face_detection
    model: yolov5
    confidence: 0.85
    device: cuda
    
  - name: object_tracking
    algorithm: deep_sort
    max_objects: 10
    
  - name: motion_analysis
    sensitivity: 0.7
    blur: 5

output:
  - type: rtsp
    port: 8554
  - type: file
    path: processed.mp4
```

### `audio_config.yaml`
```yaml
input:
  device: mic0
  rate: 44100
  channels: 2

filters:
  - name: noise_reduction
    strength: 0.8
  - name: equalizer
    bands:
      - freq: 100
        gain: -3
      - freq: 1000
        gain: 2

analysis:
  - type: feature_extraction
    window: 1024
  - type: classification
    model: yamnet
```

## Requirements

- RTASPI with processing extensions
- OpenCV with CUDA support
- TensorFlow/PyTorch
- Additional ML models

## Usage

1. Configure pipelines:
```bash
# Copy and edit configuration
cp pipeline_config.yaml.example pipeline_config.yaml
cp audio_config.yaml.example audio_config.yaml
```

2. Run examples:
```bash
# Face detection
python face_detection.py --config pipeline_config.yaml

# Motion detection
python motion_detection.py --camera 0 --sensitivity 0.8

# Object tracking
python object_tracking.py --source rtsp://camera/stream

# Audio processing
python audio_processing.py --config audio_config.yaml
```

## Features

### Video Processing
- Multiple detection models
- Real-time tracking
- Filter chains
- Performance optimization

### Audio Processing
- Real-time filtering
- Feature extraction
- Pattern recognition
- Stream synchronization

### Pipeline Management
- Dynamic reconfiguration
- Resource monitoring
- Error recovery
- Performance metrics

### Output Options
- Multiple formats
- Network streaming
- File recording
- Analytics export

## Best Practices

1. Pipeline Design
   - Optimize processing order
   - Balance accuracy/speed
   - Handle errors gracefully
   - Monitor resources

2. Performance
   - Use GPU acceleration
   - Optimize resolution
   - Buffer management
   - Parallel processing

3. Development
   - Test components
   - Profile performance
   - Document pipelines
   - Version control

## Model Management

### Video Models
- Face detection
- Object detection
- Pose estimation
- Action recognition

### Audio Models
- Speech recognition
- Sound classification
- Voice activity
- Emotion detection

### Management
- Model versioning
- Cache handling
- Memory optimization
- Auto-updates

## Troubleshooting

Common issues and solutions:

1. Performance Issues
   - Check GPU utilization
   - Optimize resolution
   - Adjust buffer sizes
   - Profile bottlenecks

2. Detection Problems
   - Verify model compatibility
   - Check input quality
   - Adjust parameters
   - Update models

3. Pipeline Errors
   - Check configurations
   - Monitor resources
   - Handle exceptions
   - Log issues

## Support

For pipeline-related issues:
- Check documentation
- Join processing channel on Discord
- Submit detailed bug reports
- Share optimizations
