"""
Constants and enumerations for video resolutions supported by the system.
"""

from enum import Enum, auto

# Resolution string constants
RES_QVGA = "320x240"       # Quarter VGA
RES_VGA = "640x480"        # VGA
RES_SVGA = "800x600"       # Super VGA
RES_XGA = "1024x768"       # Extended Graphics Array
RES_HD = "1280x720"        # 720p HD
RES_FULL_HD = "1920x1080"  # 1080p Full HD / 2K
RES_QHD = "2560x1440"      # Quad HD
RES_UHD_4K = "3840x2160"   # 4K Ultra HD
RES_DCI_4K = "4096x2160"   # DCI 4K (Digital Cinema)
RES_UHD_8K = "7680x4320"   # 8K Ultra HD


class Resolution(Enum):
    """Enumeration of standard video resolutions."""

    # Standard Resolutions
    QVGA = "320x240"       # Quarter VGA
    VGA = "640x480"        # VGA
    SVGA = "800x600"       # Super VGA
    XGA = "1024x768"       # Extended Graphics Array
    HD = "1280x720"        # 720p HD
    FULL_HD = "1920x1080"  # 1080p Full HD / 2K
    QHD = "2560x1440"      # Quad HD
    UHD_4K = "3840x2160"   # 4K Ultra HD
    DCI_4K = "4096x2160"   # DCI 4K (Digital Cinema)
    UHD_8K = "7680x4320"   # 8K Ultra HD

    # Common Aliases
    RES_720P = HD
    RES_1080P = FULL_HD
    RES_2K = FULL_HD
    RES_4K = UHD_4K
    RES_8K = UHD_8K

    @classmethod
    def standard_resolutions(cls) -> list["Resolution"]:
        """Return a list of standard resolutions."""
        return [
            cls.QVGA,
            cls.VGA,
            cls.SVGA,
            cls.XGA,
            cls.HD,
            cls.FULL_HD,
            cls.QHD,
            cls.UHD_4K,
            cls.DCI_4K,
            cls.UHD_8K,
        ]

    @classmethod
    def hd_resolutions(cls) -> list["Resolution"]:
        """Return a list of HD and above resolutions."""
        return [
            cls.HD,
            cls.FULL_HD,
            cls.QHD,
            cls.UHD_4K,
            cls.DCI_4K,
            cls.UHD_8K,
        ]

    def is_hd(self) -> bool:
        """Check if this is an HD or higher resolution."""
        return self in self.hd_resolutions()

    def get_dimensions(self) -> tuple[int, int]:
        """Return the width and height as integers."""
        width, height = self.value.split("x")
        return int(width), int(height)

    def get_width(self) -> int:
        """Return the width as an integer."""
        return self.get_dimensions()[0]

    def get_height(self) -> int:
        """Return the height as an integer."""
        return self.get_dimensions()[1]

    def get_aspect_ratio(self) -> float:
        """Return the aspect ratio as a float."""
        width, height = self.get_dimensions()
        return width / height
