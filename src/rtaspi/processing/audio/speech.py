"""
Speech recognition implementation.

This module provides speech recognition capabilities using various engines:
- Local recognition using Vosk
- Cloud recognition using Google Speech-to-Text
- Keyword spotting
"""

import json
import wave
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import numpy as np

try:
    from vosk import Model, KaldiRecognizer, SetLogLevel

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    from google.cloud import speech

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class SpeechRecognizer:
    """Speech recognition using various engines."""

    def __init__(
        self,
        engine: str = "vosk",
        model_path: Optional[str] = None,
        language: str = "en-US",
        credentials_path: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ):
        """Initialize the speech recognizer.

        Args:
            engine: Recognition engine ("vosk" or "google")
            model_path: Path to Vosk model directory
            language: Recognition language
            credentials_path: Path to Google credentials JSON
            keywords: List of keywords to spot
        """
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.language = language
        self.keywords = keywords or []

        if engine == "vosk":
            if not VOSK_AVAILABLE:
                raise ImportError("Vosk is not installed")

            # Load Vosk model
            if not model_path:
                model_path = str(
                    Path(__file__).parent / "models" / "vosk-model-small-en"
                )

            SetLogLevel(-1)  # Disable Kaldi logging
            self.model = Model(model_path)
            self.recognizer = None  # Created per audio stream

        elif engine == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError("Google Cloud Speech-to-Text is not installed")

            # Initialize Google client
            if credentials_path:
                self.client = speech.SpeechClient.from_service_account_file(
                    credentials_path
                )
            else:
                self.client = speech.SpeechClient()

        else:
            raise ValueError(f"Unsupported engine: {engine}")

    def recognize(
        self, audio: Union[np.ndarray, bytes], sample_rate: int, partial: bool = False
    ) -> Dict[str, Any]:
        """Recognize speech in audio.

        Args:
            audio: Audio data (numpy array or bytes)
            sample_rate: Audio sample rate in Hz
            partial: Whether to return partial results

        Returns:
            Recognition results
        """
        if self.engine == "vosk":
            return self._recognize_vosk(audio, sample_rate, partial)
        else:  # google
            return self._recognize_google(audio, sample_rate)

    def _recognize_vosk(
        self, audio: Union[np.ndarray, bytes], sample_rate: int, partial: bool
    ) -> Dict[str, Any]:
        """Recognize speech using Vosk.

        Args:
            audio: Audio data (numpy array or bytes)
            sample_rate: Audio sample rate in Hz
            partial: Whether to return partial results

        Returns:
            Recognition results
        """
        # Create recognizer if needed
        if not self.recognizer:
            self.recognizer = KaldiRecognizer(self.model, sample_rate)
            if self.keywords:
                self.recognizer.SetWords(True)

        # Convert audio to bytes if needed
        if isinstance(audio, np.ndarray):
            audio = (audio * 32767).astype(np.int16).tobytes()

        # Process audio
        if self.recognizer.AcceptWaveform(audio):
            result = json.loads(self.recognizer.Result())
        elif partial:
            result = json.loads(self.recognizer.PartialResult())
        else:
            result = {"text": ""}

        # Check for keywords
        if self.keywords and result.get("text"):
            words = result.get("result", [])
            keywords_found = []

            for word in words:
                if word.get("word", "").lower() in self.keywords:
                    keywords_found.append(
                        {
                            "keyword": word["word"],
                            "start": word["start"],
                            "end": word["end"],
                            "confidence": word["conf"],
                        }
                    )

            result["keywords"] = keywords_found

        return result

    def _recognize_google(
        self, audio: Union[np.ndarray, bytes], sample_rate: int
    ) -> Dict[str, Any]:
        """Recognize speech using Google Speech-to-Text.

        Args:
            audio: Audio data (numpy array or bytes)
            sample_rate: Audio sample rate in Hz

        Returns:
            Recognition results
        """
        # Convert audio to bytes if needed
        if isinstance(audio, np.ndarray):
            audio = (audio * 32767).astype(np.int16).tobytes()

        # Create recognition config
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=self.language,
            enable_word_time_offsets=bool(self.keywords),
        )

        # Create recognition audio
        audio = speech.RecognitionAudio(content=audio)

        # Perform recognition
        response = self.client.recognize(config=config, audio=audio)

        # Process results
        result = {"text": "", "confidence": 0.0, "alternatives": []}

        for i, res in enumerate(response.results):
            alt = res.alternatives[0]
            if i == 0:
                result["text"] = alt.transcript
                result["confidence"] = alt.confidence

            result["alternatives"].append(
                {"text": alt.transcript, "confidence": alt.confidence}
            )

            # Check for keywords
            if self.keywords and alt.words:
                keywords_found = []

                for word in alt.words:
                    if word.word.lower() in self.keywords:
                        keywords_found.append(
                            {
                                "keyword": word.word,
                                "start": word.start_time.total_seconds(),
                                "end": word.end_time.total_seconds(),
                                "confidence": alt.confidence,
                            }
                        )

                if keywords_found:
                    result.setdefault("keywords", []).extend(keywords_found)

        return result

    def save_audio(self, audio: np.ndarray, sample_rate: int, path: str) -> None:
        """Save audio to WAV file.

        Args:
            audio: Audio data
            sample_rate: Audio sample rate in Hz
            path: Output file path
        """
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Save as WAV
        with wave.open(path, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(audio_int16.tobytes())

        self.logger.info(f"Saved audio to: {path}")

    def load_audio(self, path: str) -> tuple[np.ndarray, int]:
        """Load audio from WAV file.

        Args:
            path: Input file path

        Returns:
            Tuple of (audio data, sample rate)
        """
        # Load WAV file
        with wave.open(path, "rb") as f:
            # Get audio properties
            channels = f.getnchannels()
            width = f.getsampwidth()
            rate = f.getframerate()
            frames = f.readframes(f.getnframes())

        # Convert to numpy array
        audio = np.frombuffer(frames, dtype=np.int16)

        # Convert to float32 and normalize
        audio = audio.astype(np.float32) / 32767.0

        # Convert to mono if needed
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        return audio, rate
