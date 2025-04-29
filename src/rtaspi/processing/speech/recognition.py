"""Speech recognition module using Whisper."""

import logging
import threading
import queue
import time
from typing import Optional, Dict, List, Callable
import numpy as np
import torch
import whisper

from ...core.logging import get_logger
from ..audio.filters import AudioFilter, NoiseReductionFilter, NormalizationFilter

logger = get_logger(__name__)

class SpeechRecognizer:
    """Speech recognition using Whisper."""

    def __init__(self, 
                 model_name: str = "base",
                 language: Optional[str] = None,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu",
                 filters: Optional[List[AudioFilter]] = None):
        """Initialize speech recognizer.
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            language: Language code (e.g., "en", "de", "pl") or None for auto-detect
            device: Device to run model on ("cuda" or "cpu")
            filters: List of audio filters to apply before recognition
        """
        self.model_name = model_name
        self.language = language
        self.device = device
        
        # Initialize Whisper model
        logger.info(f"Loading Whisper model '{model_name}' on {device}")
        self.model = whisper.load_model(model_name).to(device)
        
        # Audio preprocessing
        self.filters = filters or [
            NoiseReductionFilter(),
            NormalizationFilter()
        ]
        
        # Recognition thread
        self._recognition_thread: Optional[threading.Thread] = None
        self._stop_recognition = threading.Event()
        self._audio_queue = queue.Queue()
        
        # Callbacks
        self._on_transcription: Optional[Callable[[str], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    def start(self) -> None:
        """Start speech recognition."""
        if self._recognition_thread and self._recognition_thread.is_alive():
            logger.warning("Speech recognition already running")
            return

        self._stop_recognition.clear()
        self._recognition_thread = threading.Thread(target=self._recognition_loop)
        self._recognition_thread.daemon = True
        self._recognition_thread.start()
        logger.info("Started speech recognition")

    def stop(self) -> None:
        """Stop speech recognition."""
        if self._recognition_thread:
            self._stop_recognition.set()
            self._recognition_thread.join()
            self._recognition_thread = None
            logger.info("Stopped speech recognition")

    def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> None:
        """Process audio data for recognition.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Audio sample rate in Hz
        """
        try:
            # Apply audio filters
            filtered_audio = audio_data
            for filter in self.filters:
                filtered_audio = filter.process(filtered_audio, sample_rate)

            # Add to queue
            self._audio_queue.put((filtered_audio, sample_rate))

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            if self._on_error:
                self._on_error(e)

    def _recognition_loop(self) -> None:
        """Main recognition loop."""
        while not self._stop_recognition.is_set():
            try:
                # Get audio from queue with timeout
                try:
                    audio_data, sample_rate = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Convert to float32 if needed
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)

                # Perform recognition
                result = self.model.transcribe(
                    audio_data,
                    language=self.language,
                    task="transcribe",
                    fp16=torch.cuda.is_available()
                )

                # Extract text
                text = result["text"].strip()
                if text and self._on_transcription:
                    self._on_transcription(text)

            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                if self._on_error:
                    self._on_error(e)
                time.sleep(1)  # Avoid tight loop on error

    def set_on_transcription(self, callback: Callable[[str], None]) -> None:
        """Set callback for transcription results.
        
        Args:
            callback: Function to call with transcribed text
        """
        self._on_transcription = callback

    def set_on_error(self, callback: Callable[[Exception], None]) -> None:
        """Set callback for errors.
        
        Args:
            callback: Function to call with error
        """
        self._on_error = callback

    def set_language(self, language: Optional[str]) -> None:
        """Set recognition language.
        
        Args:
            language: Language code or None for auto-detect
        """
        self.language = language
        logger.info(f"Set recognition language to {language or 'auto'}")

    def get_available_languages(self) -> List[str]:
        """Get list of available languages.
        
        Returns:
            List[str]: List of language codes
        """
        return whisper.tokenizer.LANGUAGES.keys()

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model.
        
        Returns:
            Dict[str, Any]: Model information
        """
        return {
            'name': self.model_name,
            'language': self.language or 'auto',
            'device': self.device,
            'filters': [f.__class__.__name__ for f in self.filters]
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        if hasattr(self.model, 'cleanup'):
            self.model.cleanup()
