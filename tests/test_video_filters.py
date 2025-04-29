import pytest
import numpy as np
import cv2
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.constants import FilterType


@pytest.fixture
def sample_frame():
    # Create a sample 100x100 RGB frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    # Add some color to test color-based filters
    frame[25:75, 25:75] = [255, 128, 64]  # BGR format
    return frame


def test_grayscale_filter(sample_frame):
    filter = VideoFilter(FilterType.GRAYSCALE)
    result = filter.apply(sample_frame)

    assert result.shape == (100, 100)  # Grayscale should be 2D
    assert result.dtype == np.uint8
    assert len(result.shape) == 2  # Grayscale has no color channels


def test_edge_detection_filter(sample_frame):
    params = {"threshold1": 100, "threshold2": 200, "aperture_size": 3}
    filter = VideoFilter(FilterType.EDGE_DETECTION, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    # Edge detection should produce binary-like output
    assert np.all(np.unique(result) <= 255)
    assert np.all(np.unique(result) >= 0)


def test_blur_filter(sample_frame):
    params = {"kernel_size": 5, "sigma": 1.0}
    filter = VideoFilter(FilterType.BLUR, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    # Blurred image should have less variance than original
    assert np.var(result) < np.var(sample_frame)


def test_sharpen_filter(sample_frame):
    params = {"amount": 1.0}
    filter = VideoFilter(FilterType.SHARPEN, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    # Sharpened image should have more variance than original
    assert np.var(result) > np.var(sample_frame)


def test_color_balance_filter(sample_frame):
    params = {"red": 1.2, "green": 0.8, "blue": 1.0}
    filter = VideoFilter(FilterType.COLOR_BALANCE, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8

    # Check color channel adjustments
    b1, g1, r1 = cv2.split(sample_frame)
    b2, g2, r2 = cv2.split(result)
    assert np.mean(r2) > np.mean(r1)  # Red increased
    assert np.mean(g2) < np.mean(g1)  # Green decreased
    assert np.allclose(np.mean(b2), np.mean(b1), rtol=0.1)  # Blue unchanged


def test_brightness_filter(sample_frame):
    params = {"amount": 0.5}  # Increase brightness
    filter = VideoFilter(FilterType.BRIGHTNESS, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    assert np.mean(result) > np.mean(sample_frame)


def test_contrast_filter(sample_frame):
    params = {"amount": 1.5}  # Increase contrast
    filter = VideoFilter(FilterType.CONTRAST, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    assert np.std(result) > np.std(sample_frame)


def test_saturation_filter(sample_frame):
    params = {"amount": 1.5}  # Increase saturation
    filter = VideoFilter(FilterType.SATURATION, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8

    # Convert to HSV to check saturation
    hsv_orig = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2HSV)
    hsv_result = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    assert np.mean(hsv_result[:, :, 1]) > np.mean(hsv_orig[:, :, 1])


def test_hue_filter(sample_frame):
    params = {"amount": 30}  # Shift hue by 30 degrees
    filter = VideoFilter(FilterType.HUE, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8

    # Convert to HSV to check hue
    hsv_orig = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2HSV)
    hsv_result = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    # Account for hue wrapping around 180
    hue_diff = (np.mean(hsv_result[:, :, 0]) - np.mean(hsv_orig[:, :, 0])) % 180
    assert abs(hue_diff - 30) < 1


def test_gamma_filter(sample_frame):
    params = {"gamma": 2.0}  # Increase gamma
    filter = VideoFilter(FilterType.GAMMA, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    # Gamma > 1 should darken the image
    assert np.mean(result) < np.mean(sample_frame)


def test_threshold_filter(sample_frame):
    params = {"threshold": 128, "max_value": 255, "method": cv2.THRESH_BINARY}
    filter = VideoFilter(FilterType.THRESHOLD, params)
    result = filter.apply(sample_frame)

    assert result.shape == sample_frame.shape
    assert result.dtype == np.uint8
    # Binary threshold should only have two values
    unique_values = np.unique(result)
    assert len(unique_values) <= 2
    assert np.all(unique_values >= 0)
    assert np.all(unique_values <= 255)


def test_noise_reduction_filter(sample_frame):
    # Test all noise reduction methods
    methods = ["gaussian", "median", "bilateral"]
    for method in methods:
        params = {"method": method, "kernel_size": 5, "strength": 7}
        filter = VideoFilter(FilterType.NOISE_REDUCTION, params)
        result = filter.apply(sample_frame)

        assert result.shape == sample_frame.shape
        assert result.dtype == np.uint8
        # Noise reduction should reduce variance
        assert np.var(result) < np.var(sample_frame)


def test_invalid_filter_type():
    with pytest.raises(ValueError):
        filter = VideoFilter(FilterType.GRAYSCALE)
        filter.filter_type = "invalid_filter"  # Force an invalid type
        filter.apply(np.zeros((10, 10, 3), dtype=np.uint8))


def test_invalid_noise_reduction_method(sample_frame):
    filter = VideoFilter(FilterType.NOISE_REDUCTION, {"method": "invalid"})
    with pytest.raises(ValueError):
        filter.apply(sample_frame)


def test_default_parameters():
    # Test that filters work with default parameters
    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    frame[20:30, 20:30] = [128, 128, 128]  # Add some non-zero values

    # Only test video filters
    video_filters = [
        FilterType.GRAYSCALE,
        FilterType.EDGE_DETECTION,
        FilterType.BLUR,
        FilterType.SHARPEN,
        FilterType.COLOR_BALANCE,
        FilterType.BRIGHTNESS,
        FilterType.CONTRAST,
        FilterType.SATURATION,
        FilterType.HUE,
        FilterType.GAMMA,
        FilterType.THRESHOLD,
        FilterType.NOISE_REDUCTION,
        FilterType.FACE_DETECTION,
        FilterType.MOTION_DETECTION,
    ]

    for filter_type in video_filters:
        filter = VideoFilter(filter_type)
        result = filter.apply(frame)
        assert result.dtype == np.uint8
        if filter_type != FilterType.GRAYSCALE:
            assert result.shape == frame.shape
