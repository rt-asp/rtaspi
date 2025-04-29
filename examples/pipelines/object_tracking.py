#!/usr/bin/env python3
"""
Object Tracking Pipeline Example
Shows how to use RTASPI for multi-object tracking and classification
"""

import argparse
import cv2
import numpy as np
from rtaspi.quick.camera import Camera
from rtaspi.processing.video.detection import ObjectDetector, ObjectTracker
from rtaspi.streaming.output import StreamOutput, FileOutput

class ObjectTrackingPipeline:
    def __init__(self, model='yolov5', confidence=0.5, max_objects=10):
        # Initialize detector and tracker
        self.detector = ObjectDetector(
            model=model,
            confidence=confidence
        )
        self.tracker = ObjectTracker(
            algorithm='deep_sort',
            max_objects=max_objects
        )
        
        # Initialize tracking history
        self.track_history = {}  # track_id -> list of points
        self.colors = {}  # track_id -> color
        
        # Class labels for visualization
        self.labels = self.detector.get_class_labels()
    
    def process_frame(self, frame):
        """Process frame with detection and tracking"""
        # Detect objects
        detections = self.detector.detect(frame)
        
        # Update tracker
        tracks = self.tracker.update(detections, frame)
        
        # Process each track
        for track in tracks:
            self._process_track(frame, track)
            
        # Draw tracking paths
        self._draw_paths(frame)
        
        return frame
    
    def _process_track(self, frame, track):
        """Process a single tracking result"""
        track_id = track['id']
        bbox = track['bbox']
        class_id = track['class_id']
        confidence = track['confidence']
        
        # Get or generate color for this track
        if track_id not in self.colors:
            self.colors[track_id] = self._generate_color()
        color = self.colors[track_id]
        
        # Update track history
        center = self._get_bbox_center(bbox)
        if track_id not in self.track_history:
            self.track_history[track_id] = []
        self.track_history[track_id].append(center)
        
        # Limit history length
        if len(self.track_history[track_id]) > 30:
            self.track_history[track_id].pop(0)
        
        # Draw bounding box
        x1, y1, x2, y2 = bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"{self.labels[class_id]} {confidence:.2f}"
        cv2.putText(frame, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def _draw_paths(self, frame):
        """Draw tracking paths for all objects"""
        for track_id, points in self.track_history.items():
            if len(points) < 2:
                continue
                
            color = self.colors[track_id]
            
            # Draw path
            for i in range(1, len(points)):
                pt1 = tuple(map(int, points[i-1]))
                pt2 = tuple(map(int, points[i]))
                cv2.line(frame, pt1, pt2, color, 2)
    
    def _get_bbox_center(self, bbox):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return [(x1 + x2) // 2, (y1 + y2) // 2]
    
    def _generate_color(self):
        """Generate random color for new track"""
        return tuple(map(int, np.random.randint(0, 255, 3)))

def main():
    parser = argparse.ArgumentParser(description='Object Tracking Pipeline')
    parser.add_argument('--source', type=str, default='0',
                       help='Video source (camera index or RTSP URL)')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Detection confidence threshold')
    parser.add_argument('--max-objects', type=int, default=10,
                       help='Maximum number of objects to track')
    args = parser.parse_args()
    
    # Setup camera
    try:
        source = int(args.source)
    except ValueError:
        source = args.source
    
    camera = Camera(device=source)
    pipeline = ObjectTrackingPipeline(
        confidence=args.confidence,
        max_objects=args.max_objects
    )
    
    # Setup output
    output = StreamOutput(port=8554)  # RTSP stream output
    
    try:
        print("Starting object tracking pipeline...")
        camera.start()
        
        while True:
            # Get frame
            frame = camera.read()
            if frame is None:
                continue
            
            # Process frame
            processed = pipeline.process_frame(frame)
            
            # Send to output
            output.write(processed)
            
            # Display frame (press 'q' to quit)
            cv2.imshow('Object Tracking', processed)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nStopping pipeline...")
    finally:
        camera.stop()
        output.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
