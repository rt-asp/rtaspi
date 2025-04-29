"""
Web interface implementation.

This module provides the web interface with device management, matrix view,
and configuration controls.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from aiohttp import web
from aiohttp.web import Request, Response
from jinja2 import Environment, FileSystemLoader

from rtaspi.api import DeviceAPI, StreamAPI, PipelineAPI, ServerAPI


class WebInterface:
    """Web interface handler."""

    def __init__(self, app: web.Application):
        """Initialize the web interface.

        Args:
            app: aiohttp Application instance
        """
        self.logger = logging.getLogger(__name__)
        self.app = app
        self.device_api = DeviceAPI()
        self.stream_api = StreamAPI()
        self.pipeline_api = PipelineAPI()
        self.server_api = ServerAPI()

        # Set up template engine
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)), autoescape=True
        )

    async def index_handler(self, request: Request) -> Response:
        """Handle index page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with index page
        """
        # Get device statistics
        devices = self.device_api.list_devices()
        device_stats = {
            "total": len(devices),
            "online": sum(
                1 for d in devices.values() if d.get("status", {}).get("online", False)
            ),
            "cameras": sum(
                1 for d in devices.values() if "CAMERA" in d.get("type", "")
            ),
            "microphones": sum(
                1 for d in devices.values() if "MICROPHONE" in d.get("type", "")
            ),
        }

        # Get stream statistics
        streams = self.stream_api.list_streams()
        stream_stats = {
            "total": len(streams),
            "active": sum(
                1 for s in streams.values() if s.get("status", {}).get("active", False)
            ),
            "video": sum(
                1
                for s in streams.values()
                if s.get("source", {}).get("stream_type") in ["video", "both"]
            ),
            "audio": sum(
                1
                for s in streams.values()
                if s.get("source", {}).get("stream_type") in ["audio", "both"]
            ),
        }

        # Get pipeline statistics
        pipelines = self.pipeline_api.list_pipelines()
        pipeline_stats = {
            "total": len(pipelines),
            "running": sum(
                1
                for p in pipelines.values()
                if p.get("status", {}).get("running", False)
            ),
        }

        # Render template
        template = self.env.get_template("index.html")
        html = template.render(
            device_stats=device_stats,
            stream_stats=stream_stats,
            pipeline_stats=pipeline_stats,
        )

        return web.Response(text=html, content_type="text/html")

    async def matrix_handler(self, request: Request) -> Response:
        """Handle matrix view page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with matrix view page
        """
        # Get active streams
        streams = self.stream_api.list_streams()
        active_streams = {
            name: config
            for name, config in streams.items()
            if config.get("status", {}).get("active", False)
        }

        # Group streams by type
        video_streams = {}
        audio_streams = {}

        for name, config in active_streams.items():
            stream_type = config.get("source", {}).get("stream_type")
            if stream_type in ["video", "both"]:
                video_streams[name] = config
            if stream_type in ["audio", "both"]:
                audio_streams[name] = config

        # Render template
        template = self.env.get_template("matrix.html")
        html = template.render(video_streams=video_streams, audio_streams=audio_streams)

        return web.Response(text=html, content_type="text/html")

    async def config_handler(self, request: Request) -> Response:
        """Handle configuration page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with configuration page
        """
        # Get current configuration
        server_config = self.server_api.get_config()
        server_status = self.server_api.get_status()

        # Get API tokens
        tokens = self.server_api.list_api_tokens()

        # Render template
        template = self.env.get_template("config.html")
        html = template.render(
            config=server_config, status=server_status, tokens=tokens
        )

        return web.Response(text=html, content_type="text/html")

    def _create_template_dir(self) -> None:
        """Create template directory with default templates."""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create index.html
        index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>RT-ASP Dashboard</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <a href="/">Dashboard</a>
        <a href="/matrix">Matrix View</a>
        <a href="/config">Configuration</a>
    </nav>

    <main>
        <h1>Dashboard</h1>

        <div class="stats">
            <div class="stat-box">
                <h2>Devices</h2>
                <p>Total: {{ device_stats.total }}</p>
                <p>Online: {{ device_stats.online }}</p>
                <p>Cameras: {{ device_stats.cameras }}</p>
                <p>Microphones: {{ device_stats.microphones }}</p>
            </div>

            <div class="stat-box">
                <h2>Streams</h2>
                <p>Total: {{ stream_stats.total }}</p>
                <p>Active: {{ stream_stats.active }}</p>
                <p>Video: {{ stream_stats.video }}</p>
                <p>Audio: {{ stream_stats.audio }}</p>
            </div>

            <div class="stat-box">
                <h2>Pipelines</h2>
                <p>Total: {{ pipeline_stats.total }}</p>
                <p>Running: {{ pipeline_stats.running }}</p>
            </div>
        </div>
    </main>

    <script src="/static/js/dashboard.js"></script>
</body>
</html>
        """

        # Create matrix.html
        matrix_html = """
<!DOCTYPE html>
<html>
<head>
    <title>RT-ASP Matrix View</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <a href="/">Dashboard</a>
        <a href="/matrix">Matrix View</a>
        <a href="/config">Configuration</a>
    </nav>

    <main>
        <h1>Matrix View</h1>

        <div class="video-grid">
            {% for name, stream in video_streams.items() %}
            <div class="video-cell">
                <h3>{{ name }}</h3>
                <video autoplay controls>
                    {% for output in stream.outputs %}
                    {% if output.type == "WEBRTC" %}
                    <source src="{{ output.settings.url }}" type="application/x-webrtc">
                    {% endif %}
                    {% endfor %}
                </video>
            </div>
            {% endfor %}
        </div>

        <div class="audio-grid">
            {% for name, stream in audio_streams.items() %}
            <div class="audio-cell">
                <h3>{{ name }}</h3>
                <audio autoplay controls>
                    {% for output in stream.outputs %}
                    {% if output.type == "WEBRTC" %}
                    <source src="{{ output.settings.url }}" type="application/x-webrtc">
                    {% endif %}
                    {% endfor %}
                </audio>
            </div>
            {% endfor %}
        </div>
    </main>

    <script src="/static/js/matrix.js"></script>
</body>
</html>
        """

        # Create config.html
        config_html = """
<!DOCTYPE html>
<html>
<head>
    <title>RT-ASP Configuration</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <a href="/">Dashboard</a>
        <a href="/matrix">Matrix View</a>
        <a href="/config">Configuration</a>
    </nav>

    <main>
        <h1>Configuration</h1>

        <div class="config-section">
            <h2>Server Status</h2>
            <p>Running: {{ status.running }}</p>
            <p>URL: {{ status.url }}</p>
            <p>Workers: {{ status.workers }}</p>
            <p>SSL: {{ status.ssl_enabled }}</p>
            <p>Debug: {{ status.debug }}</p>
        </div>

        <div class="config-section">
            <h2>Server Configuration</h2>
            <p>Host: {{ config.host }}</p>
            <p>Port: {{ config.port }}</p>
            <p>SSL: {{ config.ssl_enabled }}</p>
            <p>Domain: {{ config.domain or "Not configured" }}</p>
            <p>Workers: {{ config.workers }}</p>
        </div>

        <div class="config-section">
            <h2>API Tokens</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Created</th>
                    <th>Expires</th>
                    <th>Actions</th>
                </tr>
                {% for token in tokens %}
                <tr>
                    <td>{{ token.name }}</td>
                    <td>{{ token.created_at }}</td>
                    <td>{{ token.expires_at or "Never" }}</td>
                    <td>
                        <button onclick="revokeToken('{{ token.token }}')">Revoke</button>
                    </td>
                </tr>
                {% endfor %}
            </table>
            <button onclick="createToken()">Create Token</button>
        </div>
    </main>

    <script src="/static/js/config.js"></script>
</body>
</html>
        """

        # Write templates
        (template_dir / "index.html").write_text(index_html.strip())
        (template_dir / "matrix.html").write_text(matrix_html.strip())
        (template_dir / "config.html").write_text(config_html.strip())

        # Create static directory
        static_dir = Path(__file__).parent / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        # Create CSS directory
        css_dir = static_dir / "css"
        css_dir.mkdir(exist_ok=True)

        # Create style.css
        style_css = """
body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

nav {
    background: #333;
    padding: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    margin-right: 1rem;
}

main {
    padding: 2rem;
}

.stats {
    display: flex;
    gap: 2rem;
}

.stat-box {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 4px;
    flex: 1;
}

.video-grid, .audio-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.video-cell video {
    width: 100%;
    border-radius: 4px;
}

.config-section {
    margin: 2rem 0;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

button {
    padding: 0.5rem 1rem;
    background: #333;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #444;
}
        """
        (css_dir / "style.css").write_text(style_css.strip())

        # Create JavaScript directory
        js_dir = static_dir / "js"
        js_dir.mkdir(exist_ok=True)

        # Create JavaScript files
        dashboard_js = """
// Refresh stats every 5 seconds
setInterval(() => {
    fetch('/api/server/status')
        .then(response => response.json())
        .then(data => {
            // Update stats
        });
}, 5000);
        """
        (js_dir / "dashboard.js").write_text(dashboard_js.strip())

        matrix_js = """
// Handle WebRTC connections
document.querySelectorAll('video, audio').forEach(element => {
    // Set up WebRTC connection
});

// Refresh streams every 5 seconds
setInterval(() => {
    fetch('/api/streams')
        .then(response => response.json())
        .then(data => {
            // Update streams
        });
}, 5000);
        """
        (js_dir / "matrix.js").write_text(matrix_js.strip())

        config_js = """
function createToken() {
    const name = prompt('Enter token name:');
    if (name) {
        fetch('/api/server/tokens', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        })
        .then(() => location.reload());
    }
}

function revokeToken(token) {
    if (confirm('Revoke this token?')) {
        fetch(`/api/server/tokens/${token}`, {
            method: 'DELETE'
        })
        .then(() => location.reload());
    }
}
        """
        (js_dir / "config.js").write_text(config_js.strip())
