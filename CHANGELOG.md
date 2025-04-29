# Changelog

All notable changes to this project will be documented in this file.

## [0.1.24] - 2025-04-29

## [0.1.23] - 2025-04-29

### Added
- Changes in docs/SPEECH_AND_INPUT.md
- Changes in docs/TEST.md
- Changes in examples/automation/rules.json
- Changes in examples/commands/keyboard_commands.json
- Changes in examples/industrial/modbus_config.yaml
- Changes in examples/industrial/opcua_config.yaml
- Changes in examples/security/alarms_config.yaml
- Changes in examples/security/behavior_config.yaml
- Changes in src/rtaspi/automation/actions/device.py
- Changes in src/rtaspi/automation/actions/stream.py
- Changes in src/rtaspi/automation/hass.py
- Changes in src/rtaspi/automation/mqtt.py
- Changes in src/rtaspi/automation/rules.py
- Changes in src/rtaspi/automation/triggers/device.py
- Changes in src/rtaspi/automation/triggers/stream.py
- Changes in src/rtaspi/device_managers/industrial/modbus.py
- Changes in src/rtaspi/device_managers/industrial/opcua.py
- Changes in src/rtaspi/device_managers/intercom/device.py
- Changes in src/rtaspi/device_managers/remote_desktop/capture.py
- Changes in src/rtaspi/device_managers/remote_desktop/manager.py
- Changes in src/rtaspi/device_managers/remote_desktop/vnc.py
- Changes in src/rtaspi/device_managers/voip/sip.py
- Changes in src/rtaspi/input/command_processor.py
- Changes in src/rtaspi/input/keyboard.py
- Changes in src/rtaspi/processing/speech/recognition.py
- Changes in src/rtaspi/security/alarms/base.py
- Changes in src/rtaspi/security/alarms/dsc.py
- Changes in src/rtaspi/security/alarms/honeywell.py
- Changes in src/rtaspi/security/analysis/base.py
- Changes in src/rtaspi/security/analysis/motion.py
- Changes in src/rtaspi/streaming/output.py
- Changes in tests/test_audio_filters.py
- Changes in tests/test_command_processor.py
- Changes in tests/test_dsc.py
- Changes in tests/test_hass.py
- Changes in tests/test_honeywell.py
- Changes in tests/test_intercom.py
- Changes in tests/test_keyboard.py
- Changes in tests/test_modbus.py
- Changes in tests/test_motion.py
- Changes in tests/test_mqtt.py
- Changes in tests/test_opcua.py
- Changes in tests/test_remote_desktop.py
- Changes in tests/test_remote_desktop_manager.py
- Changes in tests/test_sip.py
- Changes in tests/test_speech_recognition.py
- Changes in tests/test_vnc.py
- Changes in tests/test_window_capture.py

## [0.1.22] - 2025-04-29

### Added
- Changes in TODO2.md
- Changes in examples/config/README.md
- Changes in examples/config/project.config.yaml
- Changes in examples/config/rtaspi.config.yaml
- Changes in examples/config/user.config.yaml
- Changes in src/rtaspi/core/defaults.py
- Changes in src/rtaspi/device_managers/remote_desktop/__init__.py
- Changes in src/rtaspi/device_managers/remote_desktop/base.py
- Changes in src/rtaspi/device_managers/remote_desktop/rdp.py

### Changed
- Changes in src/rtaspi/core/config.py
- Changes in src/rtaspi/schemas/__init__.py
- Changes in src/rtaspi/schemas/device.py
- Changes in src/rtaspi/schemas/stream.py

### Fixed
- Changes in src/rtaspi/schemas/pipeline.py

## [0.1.21] - 2025-04-29

### Added
- Changes in tests/test_video_filters.py

## [0.1.20] - 2025-04-29

### Changed
- Changes in src/rtaspi/device_managers/network/device_monitor.py
- Changes in src/rtaspi/device_managers/network_devices.py

## [0.1.19] - 2025-04-29

### Added
- Changes in requirements-dev.txt
- Changes in src/rtaspi/device_managers/command_handler.py
- Changes in src/rtaspi/device_managers/network/command_handler.py
- Changes in src/rtaspi/device_managers/network/device_monitor.py
- Changes in src/rtaspi/device_managers/network/state_manager.py
- Changes in src/rtaspi/device_managers/scanners/__init__.py
- Changes in src/rtaspi/device_managers/scanners/base.py
- Changes in src/rtaspi/device_managers/scanners/linux_scanner.py
- Changes in src/rtaspi/device_managers/scanners/macos_scanner.py
- Changes in src/rtaspi/device_managers/scanners/windows_scanner.py
- Changes in src/rtaspi/device_managers/stream_manager.py
- Changes in src/rtaspi/streaming/webrtc/__init__.py
- Changes in src/rtaspi/streaming/webrtc/pipeline.py
- Changes in src/rtaspi/streaming/webrtc/server.py
- Changes in src/rtaspi/streaming/webrtc/ui.py
- Changes in src/rtaspi/web/endpoints/devices.py
- Changes in src/rtaspi/web/endpoints/pipelines.py
- Changes in src/rtaspi/web/endpoints/server.py
- Changes in src/rtaspi/web/endpoints/streams.py
- Changes in src/rtaspi/web/interface/handlers.py
- Changes in tox.ini

### Changed
- Changes in src/rtaspi/device_managers/local_devices.py
- Changes in src/rtaspi/device_managers/network_devices.py
- Changes in src/rtaspi/web/api.py

### Fixed
- Changes in src/rtaspi/streaming/webrtc.py

## [0.1.18] - 2025-04-29

## [0.1.17] - 2025-04-29

### Added
- Changes in docs/API.md
- Changes in docs/CONCEPTS.md
- Changes in docs/CONFIGURATION.md
- Changes in src/rtaspi/web/acme.py

### Changed
- Changes in docs/README.md
- Changes in src/rtaspi/web/server.py

## [0.1.16] - 2025-04-29

### Added
- Changes in TODO.txt
- Changes in docs/POST/PL/1.md
- Changes in src/rtaspi/dsl/__init__.py
- Changes in src/rtaspi/dsl/executor.py
- Changes in src/rtaspi/dsl/lexer.py
- Changes in src/rtaspi/dsl/parser.py
- Changes in src/rtaspi/processing/audio/speech.py
- Changes in src/rtaspi/processing/pipeline_executor.py

### Changed
- Changes in src/rtaspi/processing/audio/filters.py

## [0.1.15] - 2025-04-29

### Added
- Changes in DONE.md
- Changes in src/rtaspi/api/devices.py
- Changes in src/rtaspi/api/pipelines.py
- Changes in src/rtaspi/api/server.py
- Changes in src/rtaspi/api/streams.py
- Changes in src/rtaspi/processing/audio/filters.py
- Changes in src/rtaspi/processing/video/detection.py
- Changes in src/rtaspi/processing/video/filters.py
- Changes in src/rtaspi/quick/camera.py
- Changes in src/rtaspi/quick/microphone.py
- Changes in src/rtaspi/quick/utils.py
- Changes in src/rtaspi/web/__init__.py
- Changes in src/rtaspi/web/api.py
- Changes in src/rtaspi/web/interface.py
- Changes in src/rtaspi/web/server.py

### Changed
- Changes in src/rtaspi/api/__init__.py
- Changes in src/rtaspi/cli/completion/bash.sh
- Changes in src/rtaspi/cli/completion/fish.fish
- Changes in src/rtaspi/cli/completion/zsh.zsh
- Changes in src/rtaspi/processing/__init__.py
- Changes in src/rtaspi/quick/__init__.py

## [0.1.14] - 2025-04-29

### Added
- Changes in src/rtaspi/api/__init__.py
- Changes in src/rtaspi/cli/__init__.py
- Changes in src/rtaspi/cli/commands/__init__.py
- Changes in src/rtaspi/cli/commands/config.py
- Changes in src/rtaspi/cli/commands/devices.py
- Changes in src/rtaspi/cli/completion/bash.sh
- Changes in src/rtaspi/cli/completion/fish.fish
- Changes in src/rtaspi/cli/completion/zsh.zsh
- Changes in src/rtaspi/cli/shell.py
- Changes in src/rtaspi/constants/__init__.py
- Changes in src/rtaspi/constants/devices.py
- Changes in src/rtaspi/constants/filters.py
- Changes in src/rtaspi/constants/outputs.py
- Changes in src/rtaspi/constants/protocols.py
- Changes in src/rtaspi/processing/__init__.py
- Changes in src/rtaspi/quick/__init__.py
- Changes in src/rtaspi/schemas/__init__.py
- Changes in src/rtaspi/schemas/device.py
- Changes in src/rtaspi/schemas/pipeline.py
- Changes in src/rtaspi/schemas/stream.py

## [0.1.13] - 2025-04-29

## [0.1.12] - 2025-04-29

### Changed
- Changes in src/rtaspi/device_managers/local_devices.py

## [0.1.11] - 2025-04-29

### Added
- Changes in rtaspi.config.yaml
- Changes in rtaspi.devices.yaml
- Changes in rtaspi.pipeline.yaml
- Changes in rtaspi.secrets.yaml
- Changes in rtaspi.streams.yaml

## [0.1.10] - 2025-04-29

## [0.1.9] - 2025-04-29

## [0.1.8] - 2025-04-29

## [0.1.7] - 2025-04-29

### Added
- Changes in .pre-commit-config.yaml
- Changes in TODO.md
- Changes in setup.cfg
- Changes in tests/conftest.py

### Fixed
- Changes in tests/test_discovery.py
- Changes in tests/test_local_devices.py
- Changes in tests/test_network_devices.py
- Changes in tests/test_streaming.py

## [0.1.6] - 2025-04-28

## [0.1.5] - 2025-04-28

### Added
- Changes in pyproject.toml

## [0.1.4] - 2025-04-28

## [0.1.3] - 2025-04-28

### Removed
- Changes in REDME.md

## [0.1.2] - 2025-04-28

### Added
- Changes in src/rtaspi/main.py

## [0.1.1] - 2025-04-28

### Added
- Changes in .flatedit
- Changes in .flatedit.logs.txt
- Changes in CONTRIBUTING.md
- Changes in MANIFEST.in
- Changes in Makefile
- Changes in REDME.md
- Changes in __init__.py
- Changes in changelog.py
- Changes in config.yaml
- Changes in docs/INSTALL.md
- Changes in docs/PROJECTS.md
- Changes in docs/PROJECTS_LOCAL.md
- Changes in docs/README.md
- Changes in docs/TREE.md
- Changes in fedora/python.sh
- Changes in flatedit.txt
- Changes in git.sh
- Changes in install/README.md
- Changes in install/SPACY.md
- Changes in install/pyaudio.py
- Changes in install/pyaudio.sh
- Changes in install/pyaudio2.py
- Changes in install/pyaudio2.sh
- Changes in install/pyaudio3.sh
- Changes in install/pyaudiodiag.py
- Changes in install/pyautogui.md
- Changes in install/pyautogui.py
- Changes in install/spacy.sh
- Changes in install/windows.ps1
- Changes in main.py
- Changes in requirements.txt
- Changes in scripts/configure_hardware.sh
- Changes in scripts/install_models.sh
- Changes in scripts/optimize_rpi.sh
- Changes in scripts/publish.sh
- Changes in scripts/setup_service.sh
- Changes in scripts/upgrade.sh
- Changes in service/start.sh
- Changes in service/stop.sh
- Changes in setup.py
- Changes in src/rtaspi/__init__.py
- Changes in src/rtaspi/__init__.py.bak
- Changes in src/rtaspi/__main__.py
- Changes in src/rtaspi/_version.py
- Changes in src/rtaspi/_version.py.bak
- Changes in src/rtaspi/config/__init__.py
- Changes in src/rtaspi/streaming/__init__.py
- Changes in src/rtaspi/streaming/rtmp.py
- Changes in src/rtaspi/streaming/rtsp.py
- Changes in src/rtaspi/streaming/utils.py
- Changes in src/rtaspi/streaming/webrtc.py
- Changes in tests/__init__.py
- Changes in tests/test_discovery.py
- Changes in tests/test_local_devices.py
- Changes in tests/test_network_devices.py
- Changes in tests/test_streaming.py
- Changes in update/duplicated.py
- Changes in update/duplicated.sh
- Changes in update/pip.sh
- Changes in update/requirements.py
- Changes in update/requirements.sh
- Changes in update/versions.py
- Changes in version.sh
- Changes in version/README.md
- Changes in version/project.py
- Changes in version/setup.py
- Changes in version/src.py

