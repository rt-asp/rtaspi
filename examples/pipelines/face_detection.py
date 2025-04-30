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
from rtaspi.core.config import ConfigManager
from rtaspi.core.mcp import MCPBroker

def setup_pipeline(config_path):
    """Setup the face detection pipeline from config"""
    with open(config_path, 'r') as f:
        pipeline_config = yaml.safe_load(f)
    
    # Initialize config and MCP broker
    config_manager = ConfigManager()
    mcp_broker = MCPBroker()
    
    # Setup input
    camera = Camera(
        device=pipeline_config['input']['source'],
        resolution=pipeline_config['input']['resolution'],
        fps=pipeline_config['input']['fps']
    )
    
    # Setup face detector
    detector = FaceDetector(
        method='dnn',
        confidence_threshold=pipeline_config['processing'][0]['confidence']
    )
    
    # Setup outputs
    outputs = []
    for output_config in pipeline_config['output']:
        if output_config['type'] == 'rtsp':
            outputs.append(StreamOutput(port=output_config['port']))
        elif output_config['type'] == 'file':
            outputs.append(FileOutput(path=output_config['path']))
    
    return camera, detector, outputs

def process_frame(frame, detector):
    """Process a single frame with face detection"""
    # Detect faces
    faces, annotated_frame = detector.detect(frame, draw=True)
    return annotated_frame

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
