#!/usr/bin/env python3
"""
Audio Processing Pipeline Example
Shows how to use RTASPI for audio filtering and analysis
"""

import argparse
import yaml
import numpy as np
from rtaspi.quick.microphone import Microphone
from rtaspi.processing.audio.filters import NoiseReducer, Equalizer
from rtaspi.processing.audio.speech import FeatureExtractor, AudioClassifier
from rtaspi.streaming.output import AudioOutput

class AudioPipeline:
    def __init__(self, config_path):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Setup filters
        self.filters = []
        for filter_config in self.config['filters']:
            if filter_config['name'] == 'noise_reduction':
                self.filters.append(
                    NoiseReducer(strength=filter_config['strength'])
                )
            elif filter_config['name'] == 'equalizer':
                self.filters.append(
                    Equalizer(bands=filter_config['bands'])
                )
        
        # Setup analysis components
        self.analyzers = []
        for analysis_config in self.config['analysis']:
            if analysis_config['type'] == 'feature_extraction':
                self.analyzers.append(
                    FeatureExtractor(window_size=analysis_config['window'])
                )
            elif analysis_config['type'] == 'classification':
                self.analyzers.append(
                    AudioClassifier(model=analysis_config['model'])
                )
                
        # Analysis results
        self.features = None
        self.classifications = []
        self.update_interval = 10  # Update analysis every N frames
        self.frame_count = 0
    
    def process_audio(self, audio_frame):
        """Process a single audio frame"""
        processed = audio_frame
        
        # Apply filters
        for audio_filter in self.filters:
            processed = audio_filter.process(processed)
        
        # Run analysis periodically
        self.frame_count += 1
        if self.frame_count % self.update_interval == 0:
            self._analyze_audio(processed)
        
        return processed
    
    def _analyze_audio(self, audio):
        """Run audio analysis"""
        # Extract features
        for analyzer in self.analyzers:
            if isinstance(analyzer, FeatureExtractor):
                self.features = analyzer.extract(audio)
            elif isinstance(analyzer, AudioClassifier):
                # Use extracted features for classification
                if self.features is not None:
                    result = analyzer.classify(self.features)
                    self.classifications.append(result)
                    # Keep last N classifications
                    if len(self.classifications) > 5:
                        self.classifications.pop(0)
    
    def get_current_analysis(self):
        """Get latest analysis results"""
        if not self.classifications:
            return "No classifications yet"
            
        # Get most common recent classification
        classes, counts = np.unique(self.classifications, return_counts=True)
        dominant_class = classes[np.argmax(counts)]
        confidence = max(counts) / len(self.classifications)
        
        return f"Audio Class: {dominant_class} ({confidence:.2f} confidence)"

def main():
    parser = argparse.ArgumentParser(description='Audio Processing Pipeline')
    parser.add_argument('--config', type=str, default='audio_config.yaml',
                       help='Path to audio configuration file')
    args = parser.parse_args()
    
    # Setup components
    pipeline = AudioPipeline(args.config)
    mic = Microphone(
        device=pipeline.config['input']['device'],
        rate=pipeline.config['input']['rate'],
        channels=pipeline.config['input']['channels']
    )
    output = AudioOutput()
    
    try:
        print("Starting audio processing pipeline...")
        mic.start()
        
        while True:
            # Get audio frame
            audio = mic.read()
            if audio is None:
                continue
            
            # Process audio
            processed = pipeline.process_audio(audio)
            
            # Output processed audio
            output.write(processed)
            
            # Print analysis periodically
            if pipeline.frame_count % 50 == 0:  # Every 50 frames
                print("\r" + pipeline.get_current_analysis(), end="")
                
    except KeyboardInterrupt:
        print("\nStopping pipeline...")
    finally:
        mic.stop()
        output.close()

if __name__ == '__main__':
    main()
