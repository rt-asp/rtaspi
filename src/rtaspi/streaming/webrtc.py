#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Obsługa protokołu WebRTC
"""

import os
import logging
import subprocess
import shlex
import time
import socket
import uuid
import json
from pathlib import Path

logger = logging.getLogger("WebRTC")


class WebRTCServer:
    """Klasa do obsługi streamingu WebRTC."""

    def __init__(self, config):
        """
        Inicjalizacja serwera WebRTC.

        Args:
            config (dict): Konfiguracja serwera.
        """
        self.config = config

        # Pobranie konfiguracji z pliku
        streaming_config = config.get('streaming', {}).get('webrtc', {})
        self.port_start = streaming_config.get('port_start', 8080)
        self.storage_path = config.get('system', {}).get('storage_path', 'storage')
        self.stun_server = streaming_config.get('stun_server', 'stun://stun.l.google.com:19302')
        self.turn_server = streaming_config.get('turn_server', '')
        self.turn_username = streaming_config.get('turn_username', '')
        self.turn_password = streaming_config.get('turn_password', '')

    def start_stream(self, device, stream_id, output_dir):
        """
        Uruchamia strumień WebRTC z lokalnego urządzenia.

        Args:
            device: Obiekt urządzenia.
            stream_id (str): Identyfikator strumienia.
            output_dir (str): Katalog wyjściowy.

        Returns:
            str: URL do strumienia WebRTC lub None w przypadku błędu.
        """
        try:
            # Wybór wolnego portu
            port = self._find_free_port(self.port_start)

            # Przygotowanie komend GStreamer w zależności od systemu i typu urządzenia
            input_pipeline = self._prepare_input_pipeline(device)
            encoding_pipeline = self._prepare_encoding_pipeline(device)

            if not input_pipeline or not encoding_pipeline:
                logger.error(f"Nie można przygotować potoku GStreamer dla urządzenia {device.device_id}")
                return None

            # Tworzenie pliku konfiguracyjnego dla GStreamer WebRTC
            gst_config_path = os.path.join(output_dir, 'webrtc_config.json')
            with open(gst_config_path, 'w') as f:
                json.dump({
                    "port": port,
                    "stream_id": stream_id,
                    "device_id": device.device_id,
                    "device_type": device.type,
                    "stun_server": self.stun_server,
                    "turn_server": self.turn_server,
                    "turn_username": self.turn_username,
                    "turn_password": self.turn_password
                }, f, indent=2)

            # Tworzenie pełnej komendy GStreamer
            gst_pipeline = f"{input_pipeline} ! {encoding_pipeline} ! webrtcbin name=webrtcbin stun-server={self.stun_server}"

            # Tworzymy plik HTML dla połączenia WebRTC
            html_content = self._generate_webrtc_html(stream_id, port)
            html_path = os.path.join(output_dir, 'webrtc.html')
            with open(html_path, 'w') as f:
                f.write(html_content)

            # Uruchomienie prostego serwera HTTP dla serwowania strony WebRTC
            http_server_cmd = ['python3', '-m', 'http.server', str(port), '--directory', output_dir]
            http_process = subprocess.Popen(
                http_server_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie na uruchomienie serwera HTTP
            time.sleep(1)

            # Uruchomienie GStreamer z pipeline dla WebRTC
            gst_cmd = ['gst-launch-1.0', '-v'] + shlex.split(gst_pipeline)
            logger.debug(f"Uruchamianie komendy: {' '.join(gst_cmd)}")

            process = subprocess.Popen(
                gst_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie, aby sprawdzić, czy proces się uruchomił
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"Proces GStreamer zakończył działanie z kodem: {process.returncode}")
                http_process.terminate()
                return None

            # Dodanie procesu do informacji o strumieniu
            url = f"http://localhost:{port}/webrtc.html?stream={stream_id}"
            stream_info = {
                "process": process,
                "http_process": http_process,
                "device_id": device.device_id,
                "type": device.type,
                "url": url,
                "protocol": "webrtc",
                "port": port
            }

            return url

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania strumienia WebRTC: {e}")
            return None

    def proxy_stream(self, device, stream_id, source_url, output_dir, transcode=False):
        """
        Uruchamia proxy WebRTC dla zdalnego strumienia.

        Args:
            device: Obiekt urządzenia sieciowego.
            stream_id (str): Identyfikator strumienia.
            source_url (str): URL źródłowy.
            output_dir (str): Katalog wyjściowy.
            transcode (bool): Czy transkodować strumień.

        Returns:
            str: URL do strumienia WebRTC lub None w przypadku błędu.
        """
        try:
            # Wybór wolnego portu
            port = self._find_free_port(self.port_start)

            # Przygotowanie komend GStreamer
            if device.protocol == 'rtsp':
                input_pipeline = f"rtspsrc location={source_url} ! rtpjitterbuffer"
            elif device.protocol == 'rtmp':
                input_pipeline = f"rtmpsrc location={source_url} ! flvdemux"
            else:
                input_pipeline = f"uridecodebin uri={source_url}"

            # Przygotowanie pipeline'u kodowania
            if transcode:
                if device.type == 'video':
                    encoding_pipeline = "decodebin ! videoconvert ! x264enc tune=zerolatency ! rtph264pay"
                    if device.protocol == 'rtsp':
                        # Dla RTSP możemy użyć istniejącego kodowania
                        encoding_pipeline = "rtph264depay ! h264parse ! rtph264pay"
                else:
                    encoding_pipeline = "decodebin ! audioconvert ! opusenc ! rtpopuspay"
                    if device.protocol == 'rtsp':
                        # Dla RTSP możemy użyć istniejącego kodowania
                        encoding_pipeline = "rtppcmadepay ! alawdec ! audioconvert ! opusenc ! rtpopuspay"
            else:
                # Bez transkodowania - próba przekazania strumienia
                if device.type == 'video':
                    if device.protocol == 'rtsp':
                        encoding_pipeline = "rtph264depay ! h264parse ! rtph264pay"
                    else:
                        encoding_pipeline = "h264parse ! rtph264pay"
                else:
                    if device.protocol == 'rtsp':
                        encoding_pipeline = "rtppcmadepay ! alawdec ! audioconvert ! opusenc ! rtpopuspay"
                    else:
                        encoding_pipeline = "audioconvert ! opusenc ! rtpopuspay"

            # Tworzenie pełnej komendy GStreamer
            gst_pipeline = f"{input_pipeline} ! {encoding_pipeline} ! webrtcbin name=webrtcbin stun-server={self.stun_server}"

            # Tworzymy plik HTML dla połączenia WebRTC
            html_content = self._generate_webrtc_html(stream_id, port)
            html_path = os.path.join(output_dir, 'webrtc.html')
            with open(html_path, 'w') as f:
                f.write(html_content)

            # Uruchomienie prostego serwera HTTP dla serwowania strony WebRTC
            http_server_cmd = ['python3', '-m', 'http.server', str(port), '--directory', output_dir]
            http_process = subprocess.Popen(
                http_server_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie na uruchomienie serwera HTTP
            time.sleep(1)

            # Uruchomienie GStreamer z pipeline dla WebRTC
            gst_cmd = ['gst-launch-1.0', '-v'] + shlex.split(gst_pipeline)
            logger.debug(f"Uruchamianie komendy proxy WebRTC: {' '.join(gst_cmd)}")

            process = subprocess.Popen(
                gst_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie, aby sprawdzić, czy proces się uruchomił
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"Proces GStreamer proxy zakończył działanie z kodem: {process.returncode}")
                http_process.terminate()
                return None

            # Utworzenie URL do strumienia
            url = f"http://localhost:{port}/webrtc.html?stream={stream_id}"

            return url

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania proxy WebRTC: {e}")
            return None

    def _prepare_input_pipeline(self, device):
        """
        Przygotowuje potok wejściowy dla GStreamer.

        Args:
            device: Obiekt urządzenia.

        Returns:
            str: Potok wejściowy GStreamer.
        """
        import platform
        system = platform.system().lower()

        if device.type == 'video':
            if system == 'linux':
                if device.driver == 'v4l2':
                    return f"v4l2src device={device.system_path} ! video/x-raw,width=640,height=480 ! videoconvert"
            elif system == 'darwin':  # macOS
                if device.driver == 'avfoundation':
                    return f"avfvideosrc device-index={device.system_path} ! video/x-raw,width=640,height=480 ! videoconvert"
            elif system == 'windows':
                if device.driver == 'dshow':
                    return f"dshowvideosrc device-name=\"{device.system_path}\" ! video/x-raw,width=640,height=480 ! videoconvert"
        elif device.type == 'audio':
            if system == 'linux':
                if device.driver == 'alsa':
                    return f"alsasrc device={device.system_path} ! audioconvert"
                elif device.driver == 'pulse':
                    return f"pulsesrc device={device.system_path} ! audioconvert"
            elif system == 'darwin':  # macOS
                if device.driver == 'avfoundation':
                    return f"avfaudiosrc device-index={device.system_path} ! audioconvert"
            elif system == 'windows':
                if device.driver == 'dshow':
                    return f"dshowaudiosrc device-name=\"{device.system_path}\" ! audioconvert"

        logger.error(f"Nieobsługiwana platforma/sterownik: {system}/{device.driver}")
        return None

    def _prepare_encoding_pipeline(self, device):
        """
        Przygotowuje potok kodowania dla GStreamer.

        Args:
            device: Obiekt urządzenia.

        Returns:
            str: Potok kodowania GStreamer.
        """
        if device.type == 'video':
            return "x264enc tune=zerolatency ! rtph264pay"
        elif device.type == 'audio':
            return "audioconvert ! audioresample ! opusenc ! rtpopuspay"

        logger.error(f"Nieobsługiwany typ urządzenia: {device.type}")
        return None

    def _generate_webrtc_html(self, stream_id, port):
        """
        Generuje kod HTML dla połączenia WebRTC.

        Args:
            stream_id (str): Identyfikator strumienia.
            port (int): Port dla połączenia WebRTC.

        Returns:
            str: Kod HTML dla połączenia WebRTC.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>rtaspi WebRTC Stream {stream_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                video {{ max-width: 100%; max-height: 80vh; }}
                audio {{ width: 100%; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>rtaspi WebRTC Stream</h1>
                <p>Stream ID: {stream_id}</p>

                <div id="mediaContainer">
                    <!-- Miejsce na strumień media -->
                </div>

                <div>
                    <button id="startButton">Start</button>
                    <button id="stopButton" disabled>Stop</button>
                </div>
            </div>

            <script>
                const mediaContainer = document.getElementById('mediaContainer');
                const startButton = document.getElementById('startButton');
                const stopButton = document.getElementById('stopButton');
                let peerConnection = null;

                async function start() {{
                    startButton.disabled = true;

                    // Pobierz parametry z URL
                    const urlParams = new URLSearchParams(window.location.search);
                    const streamId = urlParams.get('stream') || '{stream_id}';

                    try {{
                        // Utwórz element wideo lub audio
                        const mediaType = "{stream_id}".includes('video') ? 'video' : 'audio';
                        const mediaElement = document.createElement(mediaType);
                        mediaElement.controls = true;
                        mediaElement.autoplay = true;
                        mediaElement.id = 'stream';
                        mediaContainer.appendChild(mediaElement);

                        // Konfiguracja połączenia WebRTC
                        const configuration = {{
                            iceServers: [
                                {{ urls: '{self.stun_server.replace("stun://", "stun:")}' }}
                            ]
                        }};

                        peerConnection = new RTCPeerConnection(configuration);

                        // Obsługa otrzymywanych strumieni
                        peerConnection.ontrack = (event) => {{
                            console.log('Otrzymano strumień', event);
                            mediaElement.srcObject = event.streams[0];
                        }};

                        // Nawiązanie połączenia z serwerem sygnalizacyjnym
                        const wsUrl = `ws://localhost:{port}/rtc/${streamId}`;
                        const ws = new WebSocket(wsUrl);

                        ws.onopen = async () => {{
                            console.log('Połączono z serwerem sygnalizacyjnym');

                            // Utworzenie oferty SDP
                            const offer = await peerConnection.createOffer();
                            await peerConnection.setLocalDescription(offer);

                            // Wysłanie oferty do serwera
                            ws.send(JSON.stringify({{
                                type: 'offer',
                                sdp: peerConnection.localDescription
                            }}));
                        }};

                        ws.onmessage = async (event) => {{
                            const message = JSON.parse(event.data);

                            if (message.type === 'answer') {{
                                // Otrzymano odpowiedź SDP
                                await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
                            }} else if (message.type === 'candidate') {{
                                // Otrzymano kandydata ICE
                                await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
                            }}
                        }};

                        // Obsługa błędów WebSocket
                        ws.onerror = (error) => {{
                            console.error('Błąd WebSocket:', error);
                            alert('Nie można nawiązać połączenia z serwerem sygnalizacyjnym');
                        }};

                        stopButton.disabled = false;
                    }} catch (error) {{
                        console.error('Błąd podczas uruchamiania strumienia WebRTC:', error);
                        alert('Błąd podczas uruchamiania strumienia WebRTC: ' + error.message);
                        startButton.disabled = false;
                    }}
                }}

                function stop() {{
                    if (peerConnection) {{
                        peerConnection.close();
                        peerConnection = null;
                    }}

                    const mediaElement = document.getElementById('stream');
                    if (mediaElement) {{
                        mediaElement.remove();
                    }}

                    startButton.disabled = false;
                    stopButton.disabled = true;
                }}

                startButton.addEventListener('click', start);
                stopButton.addEventListener('click', stop);

                // Automatyczne uruchomienie strumienia
                window.addEventListener('load', start);
            </script>
        </body>
        </html>
        """

    def _find_free_port(self, start_port):
        """
        Znajduje wolny port zaczynając od podanego.

        Args:
            start_port (int): Port początkowy.

        Returns:
            int: Wolny port.
        """
        port = start_port
        max_port = start_port + 1000  # Ograniczenie zakresu skanowania

        while port < max_port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result != 0:  # Port jest wolny
                return port

            port += 1

        raise Exception(f"Nie znaleziono wolnego portu w zakresie {start_port}-{max_port}")