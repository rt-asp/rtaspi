"""
Example of implementing an image processing system with RTASPI
Demonstrates advantages over cloud services like AWS Rekognition/Google Vision AI
"""

from rtaspi.core import rtaspi
from rtaspi.processing.video.pipeline import VideoPipeline
from rtaspi.ml.models import ModelManager
from rtaspi.device_managers.local_devices import LocalDevicesManager
import torch
import time

class ProductQualityControl:
    def __init__(self):
        # Initialize RTASPI with local processing configuration
        self.app = rtaspi({
            "processing": {
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "batch_size": 4,
                "parallel_processing": True
            },
            "storage": {
                "defect_images": "/var/quality_control/defects",
                "reports": "/var/quality_control/reports"
            }
        })

        # Initialize model manager for local ML models
        self.model_manager = ModelManager(self.app.config)
        
        # Load custom defect detection model (trained on company-specific data)
        self.defect_model = self.model_manager.load_model(
            name="product_defect_detector",
            version="v3",
            type="object_detection",
            framework="pytorch"
        )

        # Initialize local device manager
        self.device_manager = LocalDevicesManager(self.app.config, self.app.mcp_broker)

    def setup_camera(self, camera_config):
        """Setup industrial camera for production line monitoring"""
        camera_id = self.device_manager.add_device(
            name=camera_config["name"],
            ip=camera_config["ip"],
            protocol=camera_config.get("protocol", "rtsp"),
            username=camera_config.get("username"),
            password=camera_config.get("password"),
            settings={
                "resolution": "1920x1080",
                "framerate": 30,
                "exposure": "auto",
                "focus": "auto"
            }
        )
        return camera_id

    def create_quality_pipeline(self):
        """Create video processing pipeline for quality control"""
        pipeline = VideoPipeline()

        # Image preprocessing stages
        pipeline.add_stage("resize", {
            "width": 640,
            "height": 480,
            "maintain_aspect": True
        })

        pipeline.add_stage("normalize", {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        })

        # Advanced image enhancement
        pipeline.add_stage("enhance", {
            "contrast": 1.2,
            "sharpness": 1.1,
            "denoise": {
                "method": "gaussian",
                "strength": 0.5
            }
        })

        # Custom defect detection stage
        class DefectDetectionStage:
            def __init__(self, model, app):
                self.model = model
                self.app = app
                self.product_count = 0
                self.defect_count = 0
                self.last_detection_time = time.time()
                
            def process(self, frame):
                current_time = time.time()
                if current_time - self.last_detection_time < 2.0:
                    return frame

                # Run defect detection
                with torch.no_grad():
                    predictions = self.model(frame.tensor)
                
                # Process predictions
                defects = self._analyze_predictions(predictions)
                
                if defects:
                    self.defect_count += 1
                    
                    # Annotate frame with defect information
                    for defect in defects:
                        frame.add_annotation(
                            type="rectangle",
                            coordinates=defect["bbox"],
                            color=(255, 0, 0),
                            label=f"Defect: {defect['type']} ({defect['confidence']:.2f})"
                        )
                    
                    # Save defect information
                    frame.metadata["defects"] = defects
                    
                    # Trigger quality control alert
                    self.app.trigger_event("quality_control.defect_detected", {
                        "product_id": self.product_count,
                        "defects": defects,
                        "timestamp": current_time,
                        "image": frame.get_jpeg()
                    })

                self.product_count += 1
                self.last_detection_time = current_time
                
                # Update statistics
                frame.metadata["stats"] = {
                    "products_inspected": self.product_count,
                    "defects_found": self.defect_count,
                    "defect_rate": self.defect_count / self.product_count if self.product_count > 0 else 0
                }
                
                return frame
                
            def _analyze_predictions(self, predictions):
                # Custom logic for analyzing model predictions
                # This can be customized based on specific product requirements
                defects = []
                for pred in predictions:
                    if pred["confidence"] > 0.6:
                        defects.append({
                            "type": pred["class_name"],
                            "confidence": pred["confidence"],
                            "bbox": pred["bbox"],
                            "severity": self._calculate_severity(pred)
                        })
                return defects
                
            def _calculate_severity(self, prediction):
                # Custom logic for determining defect severity
                area = (prediction["bbox"][2] - prediction["bbox"][0]) * \
                       (prediction["bbox"][3] - prediction["bbox"][1])
                confidence = prediction["confidence"]
                
                if area > 0.3 and confidence > 0.9:
                    return "high"
                elif area > 0.1 and confidence > 0.7:
                    return "medium"
                else:
                    return "low"

        # Add custom defect detection stage
        pipeline.add_custom_stage(DefectDetectionStage(self.defect_model, self.app))

        # Configure outputs
        pipeline.add_output("database", {
            "connection": "postgresql://user:pass@localhost/quality_control",
            "table": "inspections",
            "fields": [
                {"name": "timestamp", "source": "frame.timestamp"},
                {"name": "product_count", "source": "frame.metadata.stats.products_inspected"},
                {"name": "defect_count", "source": "frame.metadata.stats.defects_found"},
                {"name": "defect_rate", "source": "frame.metadata.stats.defect_rate"},
                {"name": "defect_types", "source": "frame.metadata.defects[].type"}
            ]
        })

        # Save defect images for review
        pipeline.add_output("file", {
            "when": "defect_detected",
            "directory": self.app.config["storage"]["defect_images"],
            "filename_pattern": "{timestamp}_{product_id}_{defect_type}.jpg"
        })

        # Real-time monitoring stream
        pipeline.add_output("rtsp", {
            "path": "/quality_control",
            "overlay": {
                "show_stats": True,
                "show_detections": True
            }
        })

        return pipeline

    def start_monitoring(self, camera_config):
        """Start quality control monitoring"""
        # Setup camera
        camera_id = self.setup_camera(camera_config)
        
        # Create and start processing pipeline
        pipeline = self.create_quality_pipeline()
        self.app.run_pipeline(pipeline, camera_id)
        
        # Start web interface for monitoring
        self.app.start_web_server(port=8080)
        
        print("Quality control system running...")
        print("Access monitoring interface at http://localhost:8080")

def main():
    # Create quality control system
    qc_system = ProductQualityControl()
    
    # Configure camera
    camera_config = {
        "name": "Production Line Camera",
        "ip": "192.168.1.100",
        "protocol": "rtsp",
        "username": "admin",
        "password": "secure_pass"
    }
    
    # Start monitoring
    try:
        qc_system.start_monitoring(camera_config)
        
        # Keep the application running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down quality control system...")
        qc_system.app.shutdown()

if __name__ == "__main__":
    main()
