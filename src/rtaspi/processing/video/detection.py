"""
Video detection implementations.

This module provides object and face detection using OpenCV and deep learning models:
- Object detection using YOLO
- Face detection using Haar cascades and deep learning
- Motion detection
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path


class ObjectDetector:
    """Object detection using YOLO."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        classes_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
    ):
        """Initialize the object detector.

        Args:
            model_path: Path to YOLO weights file
            config_path: Path to YOLO config file
            classes_path: Path to class names file
            confidence_threshold: Minimum confidence for detections
            nms_threshold: Non-maximum suppression threshold
        """
        # Load default model if paths not provided
        if not model_path or not config_path or not classes_path:
            model_dir = Path(__file__).parent / "models"
            model_path = model_dir / "yolov3.weights"
            config_path = model_dir / "yolov3.cfg"
            classes_path = model_dir / "coco.names"

        # Load YOLO network
        self.net = cv2.dnn.readNet(str(model_path), str(config_path))
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        # Load class names
        with open(classes_path) as f:
            self.classes = f.read().strip().split("\n")

        # Get output layer names
        self.output_layers = [
            self.net.getLayerNames()[i - 1] for i in self.net.getUnconnectedOutLayers()
        ]

    def detect(
        self, frame: np.ndarray, draw: bool = True
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """Detect objects in a frame.

        Args:
            frame: Input video frame
            draw: Whether to draw detection boxes

        Returns:
            Tuple of (detections, annotated frame)
        """
        height, width = frame.shape[:2]

        # Create blob from image
        blob = cv2.dnn.blobFromImage(
            frame, 1 / 255.0, (416, 416), swapRB=True, crop=False
        )

        # Forward pass
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        # Process detections
        class_ids = []
        confidences = []
        boxes = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > self.confidence_threshold:
                    # Scale box coordinates to frame size
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply non-maximum suppression
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.confidence_threshold, self.nms_threshold
        )

        # Prepare detections
        detections = []
        output_frame = frame.copy() if draw else frame

        for i in indices:
            i = i if isinstance(i, int) else i[0]
            box = boxes[i]
            x, y, w, h = box
            class_id = class_ids[i]
            confidence = confidences[i]

            detection = {
                "class": self.classes[class_id],
                "confidence": confidence,
                "box": box,
            }
            detections.append(detection)

            if draw:
                # Draw box
                cv2.rectangle(output_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Draw label
                label = f"{self.classes[class_id]}: {confidence:.2f}"
                cv2.putText(
                    output_frame,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

        return detections, output_frame


class FaceDetector:
    """Face detection using cascades and deep learning."""

    def __init__(
        self,
        method: str = "cascade",
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        cascade_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """Initialize the face detector.

        Args:
            method: Detection method ("cascade" or "dnn")
            model_path: Path to DNN model file
            config_path: Path to DNN config file
            cascade_path: Path to Haar cascade file
            confidence_threshold: Minimum confidence for DNN detections
        """
        self.method = method
        self.confidence_threshold = confidence_threshold

        if method == "dnn":
            # Load DNN model
            if not model_path or not config_path:
                model_dir = Path(__file__).parent / "models"
                model_path = model_dir / "res10_300x300_ssd_iter_140000.caffemodel"
                config_path = model_dir / "deploy.prototxt"

            self.net = cv2.dnn.readNet(str(model_path), str(config_path))

        else:  # cascade
            # Load Haar cascade
            if not cascade_path:
                cascade_path = (
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )

            self.cascade = cv2.CascadeClassifier(cascade_path)

    def detect(
        self, frame: np.ndarray, draw: bool = True
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """Detect faces in a frame.

        Args:
            frame: Input video frame
            draw: Whether to draw detection boxes

        Returns:
            Tuple of (detections, annotated frame)
        """
        if self.method == "dnn":
            return self._detect_dnn(frame, draw)
        else:
            return self._detect_cascade(frame, draw)

    def _detect_dnn(
        self, frame: np.ndarray, draw: bool
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """Detect faces using DNN.

        Args:
            frame: Input video frame
            draw: Whether to draw detection boxes

        Returns:
            Tuple of (detections, annotated frame)
        """
        height, width = frame.shape[:2]

        # Create blob from image
        blob = cv2.dnn.blobFromImage(
            frame, 1.0, (300, 300), [104, 117, 123], False, False
        )

        # Forward pass
        self.net.setInput(blob)
        detections = self.net.forward()

        # Process detections
        faces = []
        output_frame = frame.copy() if draw else frame

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > self.confidence_threshold:
                # Scale box coordinates to frame size
                box = detections[0, 0, i, 3:7] * [width, height, width, height]
                x1, y1, x2, y2 = box.astype(int)

                face = {"confidence": confidence, "box": [x1, y1, x2 - x1, y2 - y1]}
                faces.append(face)

                if draw:
                    # Draw box
                    cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Draw label
                    label = f"Face: {confidence:.2f}"
                    cv2.putText(
                        output_frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

        return faces, output_frame

    def _detect_cascade(
        self, frame: np.ndarray, draw: bool
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """Detect faces using Haar cascade.

        Args:
            frame: Input video frame
            draw: Whether to draw detection boxes

        Returns:
            Tuple of (detections, annotated frame)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        # Prepare detections
        detections = []
        output_frame = frame.copy() if draw else frame

        for x, y, w, h in faces:
            detection = {
                "confidence": 1.0,  # Cascade doesn't provide confidence
                "box": [x, y, w, h],
            }
            detections.append(detection)

            if draw:
                # Draw box
                cv2.rectangle(output_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Draw label
                cv2.putText(
                    output_frame,
                    "Face",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

        return detections, output_frame
