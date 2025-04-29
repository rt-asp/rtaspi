
## Struktura projektu

```
.
├── CHANGELOG.md
├── changelog.py
├── config.yaml
├── CONTRIBUTING.md
├── debug_imports.py
├── dist
│   ├── rtaspi-0.1.23-py3-none-any.whl
│   └── rtaspi-0.1.23.tar.gz
├── docs
│   ├── API.md
│   ├── CLI.md
│   ├── CONCEPTS.md
│   ├── CONFIGURATION.md
│   ├── INSTALL.md
│   ├── POST
│   │   ├── DE
│   │   ├── EN
│   │   └── PL
│   │       └── 1.md
│   ├── PROJECTS_LOCAL.md
│   ├── PROJECTS.md
│   ├── README.md
│   └── TREE.md
├── DONE.md
├── examples
├── fedora
│   └── python.sh
├── flatedit.txt
├── git.sh
├── install
│   ├── pyaudio2.py
│   ├── pyaudio2.sh
│   ├── pyaudio3.sh
│   ├── pyaudiodiag.py
│   ├── pyaudio.py
│   ├── pyaudio.sh
│   ├── pyautogui.md
│   ├── pyautogui.py
│   ├── README.md
│   ├── SPACY.md
│   ├── spacy.sh
│   └── windows.ps1
├── LICENSE
├── Makefile
├── MANIFEST.in
├── __pycache__
│   ├── __init__.cpython-311.pyc
│   ├── __init__.cpython-312.pyc
│   └── test_imports.cpython-312-pytest-8.3.5.pyc
├── pyproject.toml
├── pyproject.toml.bak
├── README.md
├── requirements.txt
├── rtaspi.config.yaml
├── rtaspi.devices.yaml
├── rtaspi.pipeline.yaml
├── rtaspi.secrets.yaml
├── rtaspi.streams.yaml
├── scripts
│   ├── configure_hardware.sh
│   ├── install_models.sh
│   ├── optimize_rpi.sh
│   ├── publish.sh
│   ├── setup_service.sh
│   └── upgrade.sh
├── service
│   ├── start.sh
│   └── stop.sh
├── setup.cfg
├── setup.py
├── src
│   ├── rtaspi
│   │   ├── api
│   │   │   ├── devices.py
│   │   │   ├── __init__.py
│   │   │   ├── pipelines.py
│   │   │   ├── server.py
│   │   │   └── streams.py
│   │   ├── cli
│   │   │   ├── commands
│   │   │   ├── completion
│   │   │   ├── __init__.py
│   │   │   └── shell.py
│   │   ├── config
│   │   │   └── __init__.py
│   │   ├── constants
│   │   │   ├── devices.py
│   │   │   ├── filters.py
│   │   │   ├── __init__.py
│   │   │   ├── outputs.py
│   │   │   └── protocols.py
│   │   ├── core
│   │   │   ├── config.py
│   │   │   ├── __init__.py
│   │   │   ├── logging.py
│   │   │   ├── mcp.py
│   │   │   ├── __pycache__
│   │   │   └── utils.py
│   │   ├── device_managers
│   │   │   ├── base.py
│   │   │   ├── __init__.py
│   │   │   ├── local_devices.py
│   │   │   ├── network_devices.py
│   │   │   ├── __pycache__
│   │   │   └── utils
│   │   ├── dsl
│   │   │   ├── executor.py
│   │   │   ├── __init__.py
│   │   │   ├── lexer.py
│   │   │   └── parser.py
│   │   ├── __init__.py
│   │   ├── __init__.py.bak
│   │   ├── __main__.py
│   │   ├── main.py
│   │   ├── processing
│   │   │   ├── audio
│   │   │   ├── __init__.py
│   │   │   ├── pipeline_executor.py
│   │   │   └── video
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── __main__.cpython-312.pyc
│   │   │   ├── main.cpython-312.pyc
│   │   │   └── _version.cpython-312.pyc
│   │   ├── quick
│   │   │   ├── camera.py
│   │   │   ├── __init__.py
│   │   │   ├── microphone.py
│   │   │   └── utils.py
│   │   ├── schemas
│   │   │   ├── device.py
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py
│   │   │   └── stream.py
│   │   ├── streaming
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   ├── rtmp.py
│   │   │   ├── rtsp.py
│   │   │   ├── utils.py
│   │   │   └── webrtc.py
│   │   ├── _version.py
│   │   ├── _version.py.bak
│   │   └── web
│   │       ├── acme.py
│   │       ├── api.py
│   │       ├── __init__.py
│   │       ├── interface.py
│   │       └── server.py
│   └── rtaspi.egg-info
│       ├── dependency_links.txt
│       ├── entry_points.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── test_imports.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_local_devices.py
│   ├── test_network_devices.py
│   └── test_streaming.py
├── TODO.md
├── TODO.txt
├── update
│   ├── duplicated.py
│   ├── duplicated.sh
│   ├── pip.sh
│   ├── requirements.py
│   ├── requirements.sh
│   └── versions.py

├── version
│   ├── project.py
│   ├── README.md
│   ├── setup.py
│   └── src.py
└── version.sh

```
