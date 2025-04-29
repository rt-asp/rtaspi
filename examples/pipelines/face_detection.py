#!/usr/bin/env python3
"""
Face Detection Pipeline Example
Shows how to use RTASPI for face detection in video streams
"""

import argparse
import yaml
from rtaspi.quick.camera import Camera
from rtaspi.processing.video.detection import FaceDetector
from rtaspi.streaming.output import StreamOutput, FileOutput

def setup_pipeline(config_path):
    """Setup the face detection pipeline from config"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup input
    camera = Camera(
        device=config['input']['source'],
        resolution=config['input']['resolution'],
        fps=config['input']['fps']
    )
    
    # Setup face detector
    detector = FaceDetector(
        model=config['processing'][0]['model'],
        confidence=config['processing'][0]['confidence'],
        device=config['processing'][0]['device']
    )
    
    # Setup outputs
    outputs = []
    for output_config in config['output']:
        if output_config['type'] == 'rtsp':
            outputs.append(StreamOutput(port=output_config['port']))
        elif output_config['type'] == 'file':
            outputs.append(FileOutput(path=output_config['path']))
    
    return camera, detector, outputs

def process_frame(frame, detector):
    """Process a single frame with face detection"""
    # Detect faces
    faces = detector.detect(frame)
    
    # Draw bounding boxes
    for face in faces:
        x1, y1, x2, y2 = face['bbox']
        confidence = face['confidence']
        
        # Draw rectangle around face
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add confidence label
        label = f"{confidence:.2f}"
        cv2.putText(frame, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame

def main():
    parser = argparse.ArgumentParser(description='Face Detection Pipeline')
    parser.add_argument('--config', type=str, default='pipeline_config.yaml',
                       help='Path to pipeline configuration file')
    args = parser.parse_args()
    
    # Setup pipeline components
    camera, detector, outputs = setup_pipeline(args.config)
    
    try:
        print("Starting face detection pipeline...")
        camera.start()
        
        while True:
            # Get frame from camera
            frame = camera.read()
            if frame is None:
                continue
                
            # Process frame
            processed = process_frame(frame, detector)
            
            # Send to outputs
            for output in outputs:
                output.write(processed)
                
    except KeyboardInterrupt:
        print("\nStopping pipeline...")
    finally:
        camera.stop()
        for output in outputs:
            output.close()

if __name__ == '__main__':
    import cv2
    main()
