"""
Video filter implementations.

This module provides video filter implementations using OpenCV, including:
- Basic filters (grayscale, blur, sharpen, etc.)
- Color adjustments (brightness, contrast, saturation, etc.)
- Edge detection
- Noise reduction
"""
import cv2
import numpy as np
from typing import Optional, Dict, Any, Tuple

from rtaspi.constants import FilterType


class VideoFilter:
    """Base class for video filters."""

    def __init__(self, filter_type: FilterType, params: Optional[Dict[str, Any]] = None):
        """Initialize the video filter.

        Args:
            filter_type: Type of filter to apply
            params: Filter-specific parameters
        """
        self.filter_type = filter_type
        self.params = params or {}

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply the filter to a video frame.

        Args:
            frame: Input video frame (BGR format)

        Returns:
            Processed video frame
        """
        if self.filter_type == FilterType.GRAYSCALE:
            return self._apply_grayscale(frame)
        elif self.filter_type == FilterType.EDGE_DETECTION:
            return self._apply_edge_detection(frame)
        elif self.filter_type == FilterType.BLUR:
            return self._apply_blur(frame)
        elif self.filter_type == FilterType.SHARPEN:
            return self._apply_sharpen(frame)
        elif self.filter_type == FilterType.COLOR_BALANCE:
            return self._apply_color_balance(frame)
        elif self.filter_type == FilterType.BRIGHTNESS:
            return self._apply_brightness(frame)
        elif self.filter_type == FilterType.CONTRAST:
            return self._apply_contrast(frame)
        elif self.filter_type == FilterType.SATURATION:
            return self._apply_saturation(frame)
        elif self.filter_type == FilterType.HUE:
            return self._apply_hue(frame)
        elif self.filter_type == FilterType.GAMMA:
            return self._apply_gamma(frame)
        elif self.filter_type == FilterType.THRESHOLD:
            return self._apply_threshold(frame)
        elif self.filter_type == FilterType.NOISE_REDUCTION:
            return self._apply_noise_reduction(frame)
        else:
            raise ValueError(f"Unsupported filter type: {self.filter_type}")

    def _apply_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """Apply grayscale filter.

        Args:
            frame: Input video frame

        Returns:
            Grayscale video frame
        """
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _apply_edge_detection(self, frame: np.ndarray) -> np.ndarray:
        """Apply edge detection filter.

        Args:
            frame: Input video frame

        Returns:
            Edge-detected video frame
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Get parameters
        threshold1 = self.params.get("threshold1", 100)
        threshold2 = self.params.get("threshold2", 200)
        aperture_size = self.params.get("aperture_size", 3)

        # Apply Canny edge detection
        edges = cv2.Canny(
            gray,
            threshold1=threshold1,
            threshold2=threshold2,
            apertureSize=aperture_size
        )

        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    def _apply_blur(self, frame: np.ndarray) -> np.ndarray:
        """Apply blur filter.

        Args:
            frame: Input video frame

        Returns:
            Blurred video frame
        """
        # Get parameters
        kernel_size = self.params.get("kernel_size", 5)
        sigma = self.params.get("sigma", 1.0)

        # Apply Gaussian blur
        return cv2.GaussianBlur(
            frame,
            ksize=(kernel_size, kernel_size),
            sigmaX=sigma,
            sigmaY=sigma
        )

    def _apply_sharpen(self, frame: np.ndarray) -> np.ndarray:
        """Apply sharpen filter.

        Args:
            frame: Input video frame

        Returns:
            Sharpened video frame
        """
        # Get parameters
        amount = self.params.get("amount", 1.0)

        # Create sharpening kernel
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])

        # Apply kernel
        sharpened = cv2.filter2D(frame, -1, kernel)

        # Blend with original based on amount
        return cv2.addWeighted(frame, 1 - amount, sharpened, amount, 0)

    def _apply_color_balance(self, frame: np.ndarray) -> np.ndarray:
        """Apply color balance filter.

        Args:
            frame: Input video frame

        Returns:
            Color-balanced video frame
        """
        # Get parameters
        red = self.params.get("red", 1.0)
        green = self.params.get("green", 1.0)
        blue = self.params.get("blue", 1.0)

        # Split channels
        b, g, r = cv2.split(frame)

        # Apply balance
        b = cv2.multiply(b, blue)
        g = cv2.multiply(g, green)
        r = cv2.multiply(r, red)

        # Merge channels
        return cv2.merge([b, g, r])

    def _apply_brightness(self, frame: np.ndarray) -> np.ndarray:
        """Apply brightness filter.

        Args:
            frame: Input video frame

        Returns:
            Brightness-adjusted video frame
        """
        # Get parameters
        amount = self.params.get("amount", 0.0)  # -1.0 to 1.0

        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Adjust value (brightness)
        if amount > 0:
            v = cv2.add(v, cv2.multiply(255 - v, amount))
        else:
            v = cv2.multiply(v, 1 + amount)

        # Merge channels and convert back to BGR
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _apply_contrast(self, frame: np.ndarray) -> np.ndarray:
        """Apply contrast filter.

        Args:
            frame: Input video frame

        Returns:
            Contrast-adjusted video frame
        """
        # Get parameters
        amount = self.params.get("amount", 1.0)  # 0.0 to 2.0

        # Apply contrast adjustment
        mean = np.mean(frame)
        return cv2.addWeighted(frame, amount, frame, 0, mean * (1 - amount))

    def _apply_saturation(self, frame: np.ndarray) -> np.ndarray:
        """Apply saturation filter.

        Args:
            frame: Input video frame

        Returns:
            Saturation-adjusted video frame
        """
        # Get parameters
        amount = self.params.get("amount", 1.0)  # 0.0 to 2.0

        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Adjust saturation
        s = cv2.multiply(s, amount)

        # Merge channels and convert back to BGR
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _apply_hue(self, frame: np.ndarray) -> np.ndarray:
        """Apply hue filter.

        Args:
            frame: Input video frame

        Returns:
            Hue-adjusted video frame
        """
        # Get parameters
        amount = self.params.get("amount", 0.0)  # -180 to 180

        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Adjust hue
        h = cv2.add(h, amount) % 180

        # Merge channels and convert back to BGR
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _apply_gamma(self, frame: np.ndarray) -> np.ndarray:
        """Apply gamma filter.

        Args:
            frame: Input video frame

        Returns:
            Gamma-adjusted video frame
        """
        # Get parameters
        gamma = self.params.get("gamma", 1.0)  # 0.1 to 10.0

        # Create lookup table
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in np.arange(0, 256)
        ]).astype("uint8")

        # Apply gamma correction
        return cv2.LUT(frame, table)

    def _apply_threshold(self, frame: np.ndarray) -> np.ndarray:
        """Apply threshold filter.

        Args:
            frame: Input video frame

        Returns:
            Thresholded video frame
        """
        # Get parameters
        threshold = self.params.get("threshold", 127)
        max_value = self.params.get("max_value", 255)
        method = self.params.get("method", cv2.THRESH_BINARY)

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply threshold
        _, thresh = cv2.threshold(gray, threshold, max_value, method)

        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def _apply_noise_reduction(self, frame: np.ndarray) -> np.ndarray:
        """Apply noise reduction filter.

        Args:
            frame: Input video frame

        Returns:
            Noise-reduced video frame
        """
        # Get parameters
        method = self.params.get("method", "gaussian")
        kernel_size = self.params.get("kernel_size", 5)
        strength = self.params.get("strength", 7)

        if method == "gaussian":
            return cv2.GaussianBlur(
                frame,
                (kernel_size, kernel_size),
                strength
            )
        elif method == "median":
            return cv2.medianBlur(frame, kernel_size)
        elif method == "bilateral":
            return cv2.bilateralFilter(
                frame,
                d=kernel_size,
                sigmaColor=strength,
                sigmaSpace=strength
            )
        else:
            raise ValueError(f"Unsupported noise reduction method: {method}")
