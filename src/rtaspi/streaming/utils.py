"""
Utility functions for streaming module.
"""


def get_stream_url(protocol, host, port, path="", **kwargs):
    """
    Generate a streaming URL based on the provided parameters.

    Args:
        protocol (str): Streaming protocol (rtsp, rtmp, http)
        host (str): Host address
        port (int): Port number
        path (str, optional): Stream path
        **kwargs: Additional URL parameters

    Returns:
        str: Complete streaming URL
    """
    # Build base URL
    url = f"{protocol}://{host}:{port}"

    # Add path if provided
    if path:
        # Remove leading slash if present to avoid double slashes
        if path.startswith("/"):
            path = path[1:]
        url = f"{url}/{path}"

    # Add URL parameters if any
    if kwargs:
        params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
        url = f"{url}?{params}"

    return url
