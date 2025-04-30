"""
Tests for example files to ensure they work correctly and serve as good documentation.
"""

import pytest
import importlib.util
import os
import sys
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock
from rtaspi_devices import DeviceManager
from rtaspi_devices.network import NetworkDeviceManager
from rtaspi_devices.events import EventSystem

def find_example_files(base_dir='examples'):
    """Find all Python example files."""
    example_files = []
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), base_dir)
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                example_files.append(os.path.join(root, file))
    
    return example_files

@pytest.mark.asyncio
async def test_quick_start_example():
    """Test the quick start example functionality."""
    # Mock device discovery
    mock_device = {
        'id': 'test-device-1',
        'name': 'Test Camera',
        'type': 'video',
        'status': 'online'
    }
    
    # Mock event handlers
    events = EventSystem()
    device_discovered = []
    status_changes = []
    stream_started = []
    
    async def handle_device_discovered(event_type, data):
        device_discovered.append(data)
    
    async def handle_device_status(event_type, data):
        status_changes.append((data["device_id"], data["status"]))
    
    async def handle_stream_started(event_type, data):
        stream_started.append(data)
    
    # Register handlers
    events.on("device.discovered", handle_device_discovered)
    events.on("device.status", handle_device_status)
    events.on("stream.started", handle_stream_started)
    
    # Create test config
    config = {
        "system": {
            "storage_path": "test_storage",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": ["192.168.1.0/24"],
                    "protocols": ["rtsp", "onvif"]
                }
            },
            "local": {
                "enabled": True,
                "auto_connect": True,
                "drivers": ["v4l2", "alsa"]
            }
        }
    }
    
    # Mock DeviceManager
    with patch('rtaspi_devices.DeviceManager') as MockDeviceManager:
        manager_instance = MockDeviceManager.return_value
        manager_instance.get_devices.return_value = {'test-device-1': MagicMock()}
        
        # Create manager with mocked dependencies
        manager = NetworkDeviceManager(config, events=events)
        
        # Simulate device discovery
        await events.emit("device.discovered", mock_device)
        assert len(device_discovered) == 1
        assert device_discovered[0]['id'] == 'test-device-1'
        
        # Simulate status change
        await events.emit("device.status", {"device_id": "test-device-1", "status": "recording"})
        assert len(status_changes) == 1
        assert status_changes[0] == ("test-device-1", "recording")
        
        # Simulate stream start
        stream_info = {
            'id': 'stream-1',
            'device_id': 'test-device-1',
            'format': 'h264'
        }
        await events.emit("stream.started", stream_info)
        assert len(stream_started) == 1
        assert stream_started[0]['id'] == 'stream-1'

@pytest.mark.asyncio
async def test_network_discovery_example():
    """Test the network device discovery example."""
    # Mock network discovery
    mock_devices = [
        {
            'id': 'camera-1',
            'name': 'IP Camera 1',
            'type': 'video',
            'protocol': 'rtsp',
            'ip': '192.168.1.100',
            'port': 554,
            'status': 'online',
            'capabilities': {
                'ptz': True,
                'audio': True,
                'night_vision': True
            }
        },
        {
            'id': 'camera-2',
            'name': 'IP Camera 2',
            'type': 'video',
            'protocol': 'onvif',
            'ip': '192.168.1.101',
            'port': 80,
            'status': 'online',
            'capabilities': {
                'ptz': False,
                'audio': False,
                'night_vision': True
            }
        },
        {
            'id': 'mic-1',
            'name': 'Network Microphone',
            'type': 'audio',
            'protocol': 'http',
            'ip': '192.168.1.102',
            'port': 8000,
            'status': 'online',
            'capabilities': {
                'stereo': True,
                'noise_reduction': True
            }
        }
    ]
    
    # Create test config
    config = {
        "system": {
            "storage_path": "storage/devices",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": [
                        "192.168.1.0/24",
                        "10.0.0.0/24"
                    ],
                    "protocols": [
                        "rtsp",
                        "onvif",
                        "http",
                        "mdns"
                    ],
                    "scan_interval": 30,
                    "timeout": 5,
                    "parallel_scans": 10
                }
            }
        }
    }
    
    # Create event system and handlers
    events = EventSystem()
    discovered_devices = []
    status_changes = []
    device_errors = []
    
    async def handle_device_discovered(event_type, data):
        discovered_devices.append(data)
    
    async def handle_device_status(event_type, data):
        status_changes.append((data["device_id"], data["status"]))
    
    async def handle_device_error(event_type, data):
        device_errors.append((event_type, data))
    
    events.on("device.discovered", handle_device_discovered)
    events.on("device.status", handle_device_status)
    events.on("device.error", handle_device_error)
    
    # Mock DiscoveryService
    with patch('rtaspi_devices.discovery.DiscoveryService') as MockDiscoveryService:
        discovery_instance = MockDiscoveryService.return_value
        discovery_instance.scan = AsyncMock(return_value=mock_devices)
        
        # Create discovery service
        discovery = MockDiscoveryService(config["devices"]["network"]["discovery"])
        
        # Test initial discovery
        discovered = await discovery.scan()
        assert len(discovered) == 3
        assert discovered[0]['protocol'] == 'rtsp'
        assert discovered[1]['protocol'] == 'onvif'
        assert discovered[2]['protocol'] == 'http'
        
        # Test device capabilities
        assert discovered[0]['capabilities']['ptz'] is True
        assert discovered[1]['capabilities']['night_vision'] is True
        assert discovered[2]['capabilities']['stereo'] is True
        
        # Test device type counting
        device_types = {}
        for device in discovered:
            device_type = device['type']
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        assert device_types['video'] == 2
        assert device_types['audio'] == 1
        
        # Test error handling
        error_device = {
            'id': 'error-device',
            'name': 'Error Device',
            'type': 'unknown',
            'status': 'error'
        }
        await events.emit("device.error", {"device_id": "error-device", "error": "Connection failed"})
        assert len(device_errors) == 1
        assert device_errors[0][0]["device_id"] == "error-device"
        assert "Connection failed" in device_errors[0][0]["error"]

def test_example_imports():
    """Test that all example files can be imported without errors."""
    example_files = find_example_files()
    
    for example_path in example_files:
        try:
            # Add example directory to path
            example_dir = os.path.dirname(example_path)
            if example_dir not in sys.path:
                sys.path.insert(0, example_dir)
            
            # Import the module
            module_name = os.path.splitext(os.path.basename(example_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, example_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # If module has test_example function, run it
            if hasattr(module, 'test_example'):
                module.test_example()
        except Exception as e:
            pytest.fail(f"Failed to import example {example_path}: {e}")
        finally:
            # Clean up sys.path
            if example_dir in sys.path:
                sys.path.remove(example_dir)

@pytest.mark.asyncio
async def test_example_scenarios():
    """Test specific scenarios from examples."""
    # Test basic device operations
    async def test_device_operations():
        config = {
            "system": {"storage_path": "test_storage"},
            "devices": {
                "network": {
                    "enabled": True,
                    "discovery": {
                        "enabled": True,
                        "scan_ranges": ["192.168.1.0/24"]
                    }
                }
            }
        }
        
        events = EventSystem()
        manager = NetworkDeviceManager(config, events=events)
        
        try:
            # Create and add a network device
            from rtaspi_devices.network import NetworkDevice
            device = NetworkDevice(
                device_id="cam1",
                name="Front Camera",
                type="video",
                ip="192.168.1.100",
                port=554,
                protocol="rtsp"
            )
            
            await manager.start()
            devices = manager.get_devices()
            assert isinstance(devices, dict)
            
            # Test device methods
            if devices:
                device_id = next(iter(devices))
                device = devices[device_id]
                
                # Test basic properties
                assert hasattr(device, 'id')
                assert hasattr(device, 'name')
                assert hasattr(device, 'type')
                
                # Test status
                status = await device.get_status()
                assert isinstance(status, str)
                
                # Test stream operations
                stream = await manager.start_stream(
                    device_id=device_id,
                    format="h264",
                    resolution="1280x720"
                )
                assert stream["id"]
                assert stream["device_id"] == device_id
                assert stream["format"] == "h264"
                
                # Test stream stop
                await manager.stop_stream(stream["id"])
                
        finally:
            await manager.stop()
    
    await test_device_operations()
    
    # Test error handling
    async def test_error_handling():
        with pytest.raises(Exception):
            # Test with invalid config
            manager = NetworkDeviceManager({})
            await manager.start()
        
        # Test with invalid stream parameters
        manager = NetworkDeviceManager({"system": {"storage_path": "test_storage"}})
        with pytest.raises(Exception):
            await manager.start_stream(
                device_id="invalid-device",
                format="invalid-format"
            )
    
    await test_error_handling()

@pytest.mark.asyncio
async def test_simple_example():
    """Test the simple example functionality."""
    config = {
        "system": {
            "storage_path": "storage",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": ["192.168.1.0/24"]
                }
            }
        }
    }
    
    # Mock device manager
    with patch('rtaspi_devices.DeviceManager') as MockDeviceManager:
        manager_instance = MockDeviceManager.return_value
        manager_instance.start = AsyncMock()
        manager_instance.stop = AsyncMock()
        manager_instance.start_stream = AsyncMock(return_value={
            "id": "stream-1",
            "device_id": "cam1",
            "format": "h264"
        })
        manager_instance.stop_stream = AsyncMock()
        
        # Create manager
        manager = NetworkDeviceManager(config)
        
        # Create network device
        from rtaspi_devices.network import NetworkDevice
        device = NetworkDevice(
            device_id="cam1",
            name="Front Camera",
            type="video",
            ip="192.168.1.100",
            port=554,
            protocol="rtsp"
        )
        
        # Test device operations
        await manager.start()
        status = device.get_status()
        assert status in ["online", "offline"]
        
        # Test stream operations
        stream = await manager.start_stream(
            device_id="cam1",
            format="h264",
            resolution="1280x720"
        )
        assert stream["id"] == "stream-1"
        assert stream["device_id"] == "cam1"
        
        await manager.stop_stream(stream["id"])
        await manager.stop()

@pytest.mark.asyncio
async def test_advanced_discovery_example():
    """Test the advanced network discovery example functionality."""
    from rtaspi_devices.discovery import ProtocolHandler
    from rtaspi_devices.network import NetworkDevice
    
    # Test custom protocol handler
    class TestCustomProtocolHandler(ProtocolHandler):
        async def discover(self, ip: str, port: int):
            if port == 8000:
                return {
                    "id": f"custom_{ip}_{port}",
                    "name": "Custom Camera",
                    "type": "video",
                    "protocol": "custom",
                    "ip": ip,
                    "port": port,
                    "capabilities": {
                        "resolution": ["1280x720", "1920x1080"],
                        "formats": ["h264", "mjpeg"],
                        "features": ["ptz", "night_vision"]
                    }
                }
            elif port == 8001:
                return {
                    "id": f"custom_{ip}_{port}",
                    "name": "Custom Microphone",
                    "type": "audio",
                    "protocol": "custom",
                    "ip": ip,
                    "port": port,
                    "capabilities": {
                        "formats": ["pcm", "aac"],
                        "channels": 2,
                        "sample_rate": 44100
                    }
                }
            return None
    
    # Create test config
    config = {
        "system": {
            "storage_path": "storage/devices",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": [
                        "192.168.1.0/24",
                        "10.0.0.0/24"
                    ],
                    "protocols": [
                        "rtsp",
                        "onvif",
                        "custom"
                    ],
                    "ports": {
                        "custom": [8000, 8001]
                    },
                    "scan_interval": 30,
                    "timeout": 5,
                    "parallel_scans": 10,
                    "persistence": {
                        "enabled": True,
                        "file": "discovered_devices.json"
                    }
                }
            }
        }
    }
    
    # Create event system
    events = EventSystem()
    discovered_devices = []
    
    async def handle_device_discovered(event_type, data):
        discovered_devices.append(data)
    
    events.on("device.discovered", handle_device_discovered)
    
    # Create advanced discovery service
    with patch('rtaspi_devices.discovery.DiscoveryService') as MockDiscoveryService:
        discovery_instance = MockDiscoveryService.return_value
        
        # Mock discovered devices
        mock_devices = [
            {
                "id": "custom_192.168.1.100_8000",
                "name": "Custom Camera",
                "type": "video",
                "protocol": "custom",
                "ip": "192.168.1.100",
                "port": 8000,
                "capabilities": {
                    "resolution": ["1280x720", "1920x1080"],
                    "formats": ["h264", "mjpeg"],
                    "features": ["ptz", "night_vision"]
                }
            },
            {
                "id": "custom_192.168.1.101_8001",
                "name": "Custom Microphone",
                "type": "audio",
                "protocol": "custom",
                "ip": "192.168.1.101",
                "port": 8001,
                "capabilities": {
                    "formats": ["pcm", "aac"],
                    "channels": 2,
                    "sample_rate": 44100
                }
            }
        ]
        
        discovery_instance.scan = AsyncMock(return_value=mock_devices)
        
        # Create discovery service with custom handler
        discovery = MockDiscoveryService(config["devices"]["network"]["discovery"])
        discovery.register_protocol_handler("custom", TestCustomProtocolHandler({}))
        
        # Add filters
        discovery.add_filter(lambda d: d["type"] in ["video", "audio"])
        discovery.add_filter(
            lambda d: any(
                fmt in d.get("capabilities", {}).get("formats", [])
                for fmt in ["h264", "aac"]
            )
        )
        
        # Test discovery
        discovered = await discovery.scan()
        assert len(discovered) == 2
        
        # Test device filtering
        video_devices = [d for d in discovered if d["type"] == "video"]
        audio_devices = [d for d in discovered if d["type"] == "audio"]
        assert len(video_devices) == 1
        assert len(audio_devices) == 1
        
        # Test capabilities
        video_device = video_devices[0]
        audio_device = audio_devices[0]
        
        assert "h264" in video_device["capabilities"]["formats"]
        assert "ptz" in video_device["capabilities"]["features"]
        assert "aac" in audio_device["capabilities"]["formats"]
        assert audio_device["capabilities"]["channels"] == 2
        
        # Create device manager
        manager = NetworkDeviceManager(config, events=events)
        
        try:
            await manager.start()
            
            # Add devices to manager
            for device_info in discovered:
                device = NetworkDevice(
                    device_id=device_info["id"],
                    name=device_info["name"],
                    type=device_info["type"],
                    ip=device_info["ip"],
                    port=device_info["port"],
                    protocol=device_info["protocol"]
                )
                
                # Configure capabilities
                if "capabilities" in device_info:
                    caps = device_info["capabilities"]
                    if "resolution" in caps:
                        device.supported_resolutions = caps["resolution"]
                    if "formats" in caps:
                        device.supported_formats = caps["formats"]
                
                await manager.add_device(device)
            
            # Test device statistics
            devices = manager.get_devices()
            device_stats = {}
            
            for device in devices.values():
                device_type = device.type
                if device_type not in device_stats:
                    device_stats[device_type] = {
                        "total": 0,
                        "streaming": 0,
                        "formats": set()
                    }
                
                stats = device_stats[device_type]
                stats["total"] += 1
                stats["formats"].update(device.supported_formats)
            
            # Verify statistics
            assert device_stats["video"]["total"] == 1
            assert device_stats["audio"]["total"] == 1
            assert "h264" in device_stats["video"]["formats"]
            assert "aac" in device_stats["audio"]["formats"]
            
        finally:
            await manager.stop()

@pytest.mark.asyncio
async def test_cross_module_example():
    """Test the cross-module integration example functionality."""
    from rtaspi_devices.network import NetworkDevice
    
    # Mock core configuration
    core_config = {
        "mcp": {
            "broker": {
                "host": "localhost",
                "port": 5000
            }
        }
    }
    
    # Mock device configuration
    device_config = {
        "system": {
            "storage_path": "storage/devices",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": ["192.168.1.0/24"],
                    "protocols": ["rtsp", "onvif"]
                }
            }
        },
        "streaming": {
            "formats": ["h264", "mjpeg"],
            "port_range": {
                "start": 8000,
                "end": 9000
            }
        }
    }
    
    # Mock MCP broker
    with patch('rtaspi_core.mcp.MCPBroker') as MockMCPBroker:
        broker_instance = MockMCPBroker.return_value
        broker_instance.start = AsyncMock()
        broker_instance.stop = AsyncMock()
        broker_instance.subscribe = MagicMock()
        broker_instance.publish = AsyncMock()
        broker_instance.request = AsyncMock(return_value={
            "status": "online",
            "uptime": 3600,
            "parameters": {
                "brightness": 50,
                "contrast": 75
            }
        })
        
        # Create MCP broker
        mcp_broker = MockMCPBroker(core_config.get("mcp", {}))
        await mcp_broker.start()
        
        # Create device manager
        manager = NetworkDeviceManager(device_config, mcp_broker=mcp_broker)
        
        try:
            await manager.start()
            
            # Create and add network camera
            camera = NetworkDevice(
                device_id="cam1",
                name="Front Camera",
                type="video",
                ip="192.168.1.100",
                port=554,
                protocol="rtsp"
            )
            
            # Test stream operations
            stream = await manager.start_stream(
                device_id=camera.device_id,
                format="h264",
                resolution="1280x720"
            )
            assert stream["id"]
            assert stream["format"] == "h264"
            
            # Test MCP event subscription
            def handle_device_event(topic, payload):
                assert topic.startswith("devices/")
                assert isinstance(payload, dict)
            
            mcp_broker.subscribe("devices/+/events", handle_device_event)
            
            # Test device command
            await mcp_broker.publish(
                f"devices/{camera.device_id}/commands",
                {
                    "command": "set_parameter",
                    "parameter": "brightness",
                    "value": 50
                }
            )
            
            # Test device status request
            status = await mcp_broker.request(
                f"devices/{camera.device_id}/status",
                {}
            )
            assert status["status"] == "online"
            assert "brightness" in status["parameters"]
            
            # Test pipeline creation
            pipeline_config = {
                "input": {
                    "stream_id": stream["id"],
                    "format": "h264"
                },
                "processors": [
                    {
                        "type": "motion_detection",
                        "sensitivity": 0.5
                    },
                    {
                        "type": "object_detection",
                        "model": "yolov3",
                        "confidence": 0.7
                    }
                ],
                "output": {
                    "format": "mjpeg",
                    "port": 8080
                }
            }
            
            pipeline_id = await mcp_broker.request(
                "pipelines/create",
                pipeline_config
            )
            assert pipeline_id is not None
            
        finally:
            await manager.stop()
            await mcp_broker.stop()

def test_example_error_handling():
    """Test error handling in examples."""
    example_files = find_example_files()
    
    for example_path in example_files:
        try:
            # Import module
            module_name = os.path.splitext(os.path.basename(example_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, example_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for error handling tests
            error_handlers = [
                func for func_name, func in module.__dict__.items()
                if callable(func) and func_name.startswith('test_error_')
            ]
            
            # Execute error handling tests
            for handler in error_handlers:
                with pytest.raises(Exception):
                    handler()
                    
        except Exception as e:
            pytest.fail(f"Error handling test failed for {example_path}: {e}")

if __name__ == '__main__':
    pytest.main([__file__])
