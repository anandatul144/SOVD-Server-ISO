TODO : Create DUMMY VEHICLE for SOVD API to access and test 


### PART 1: Setup and Generate Server

## Understanding SOVD Hierarchy

SOVD has 4 entity types with specific relationships:

1. **Areas** - Physical/logical vehicle zones (your 3 areas)
2. **Components** - ECUs/control units (your individual ECUs)
3. **Apps** - Software running on components
4. **Functions** - Cross-component features (like "Adaptive Cruise Control" spanning Camera + MAB)

**Key concept**: Areas *contain* Components, but Components can belong to multiple Areas. For example, MAB appears in both ADAS and BASE - this is valid since one ECU can serve multiple systems.

## Your Structure in SOVD Terms

```
Areas (3):
├─ Navigation/ADAS
│  └─ Components: Camera, LIDAR, GOLDBOX, MAB
├─ Communication  
│  └─ Components: V2X, ECU1, ECU2, Switch, Ubuntu
└─ Base/Chassis
   └─ Components: Wheels, Brakes, Accelerator, MAB, Gearbox

Components have:
├─ identData (static info: part number, SW version)
├─ currentData (live sensor readings: speed, temperature)
├─ sysInfo (system status: CPU load, memory)
├─ faults (DTCs/error codes)
└─ operations (actions: reset, calibrate)
```

## Implementation Strategy

Create a data model file: `generated-python/server/sovd_api/vehicle_model.py`

```python
"""
Mock vehicle data model
"""

VEHICLE_DATA = {
    "areas": {
        "ADAS": {
            "id": "ADAS",
            "name": "Navigation/ADAS Systems",
            "components": ["Camera", "LIDAR", "GOLDBOX", "MAB"]
        },
        "Communication": {
            "id": "Communication",
            "name": "Communication Systems",
            "components": ["V2X", "ECU1", "ECU2", "Switch", "Ubuntu"]
        },
        "Chassis": {
            "id": "Chassis",
            "name": "Base/Chassis Systems",
            "components": ["Wheels", "Brakes", "Accelerator", "MAB", "Gearbox"]
        }
    },
    
    "components": {
        "Camera": {
            "id": "Camera",
            "name": "Front Camera Unit",
            "area": "ADAS",
            "identData": {
                "PartNumber": "CAM-2024-FWD",
                "HardwareVersion": "v2.1",
                "SoftwareVersion": "v5.3.2",
                "SerialNumber": "CAM8473629"
            },
            "currentData": {
                "OperatingTemp": 42,  # Celsius
                "FPS": 60,
                "ObjectsDetected": 5,
                "Status": "active"
            },
            "faults": []  # No active faults
        },
        
        "MAB": {
            "id": "MAB",
            "name": "Multi-Function Actuator Box",
            "areas": ["ADAS", "Chassis"],  # Shared component
            "identData": {
                "PartNumber": "MAB-2024-001",
                "SoftwareVersion": "v3.1.0",
                "SerialNumber": "MAB9382847"
            },
            "currentData": {
                "CPULoad": 45,  # Percent
                "Temperature": 68,
                "SteeringAngle": 12.5,  # Degrees
                "BrakeActuationForce": 120  # Newtons
            },
            "faults": [
                {
                    "code": "MAB001",
                    "fault_name": "Steering calibration drift detected",
                    "severity": 2,
                    "status": {"aggregatedStatus": "active"}
                }
            ]
        },
        
        "Brakes": {
            "id": "Brakes",
            "name": "Brake Control Module",
            "area": "Chassis",
            "identData": {
                "PartNumber": "BRK-2024-ABS",
                "SoftwareVersion": "v4.2.1"
            },
            "currentData": {
                "FrontLeftPressure": 850,  # PSI
                "FrontRightPressure": 845,
                "RearLeftPressure": 720,
                "RearRightPressure": 725,
                "ABSActive": False
            },
            "faults": []
        }
        
        # Add other ECUs following same pattern...
    }
}

def get_component(component_id):
    """Helper to retrieve component data"""
    return VEHICLE_DATA["components"].get(component_id)

def get_area_components(area_id):
    """Get all components in an area"""
    area = VEHICLE_DATA["areas"].get(area_id)
    if not area:
        return []
    return [get_component(comp_id) for comp_id in area["components"]]
```

## Update Controllers

Edit `sovd_api/controllers/discovery_controller.py`:

```python
from sovd_api.vehicle_model import VEHICLE_DATA, get_area_components

def entity_collection_get(entity_collection, include_schema=None):
    """List entities"""
    
    if entity_collection == "areas":
        items = [
            {
                "id": area_id,
                "name": area["name"],
                "href": f"/v1/areas/{area_id}"
            }
            for area_id, area in VEHICLE_DATA["areas"].items()
        ]
        return {"items": items}, 200
    
    elif entity_collection == "components":
        items = [
            {
                "id": comp_id,
                "name": comp["name"],
                "href": f"/v1/components/{comp_id}"
            }
            for comp_id, comp in VEHICLE_DATA["components"].items()
        ]
        return {"items": items}, 200
    
    return {"items": []}, 200
```

Edit `sovd_api/controllers/data_retrieval_controller.py`:

```python
from sovd_api.vehicle_model import get_component

def entity_collection_entity_id_data_data_id_get(
    entity_collection, entity_id, data_id, include_schema=None
):
    """Read specific data value"""
    
    if entity_collection != "components":
        return {"error": "Only components supported"}, 400
    
    component = get_component(entity_id)
    if not component:
        return {"error": "Component not found"}, 404
    
    # Try to find data in different categories
    for category in ["identData", "currentData", "sysInfo"]:
        if category in component and data_id in component[category]:
            return {
                "id": data_id,
                "data": component[category][data_id]
            }, 200
    
    return {"error": "Data not found"}, 404
```

## Test Your Vehicle Model

```bash
# List all areas
curl http://localhost:8080/v1/areas

# List all components
curl http://localhost:8080/v1/components

# Get MAB current data
curl http://localhost:8080/v1/components/MAB/data/CPULoad

# Get Camera temperature
curl http://localhost:8080/v1/components/Camera/data/OperatingTemp

# Get MAB faults
curl http://localhost:8080/v1/components/MAB/faults
```

## What You're Doing Right

- Logical grouping into areas
- Shared components (MAB) across areas reflects reality
- Mix of sensor data (readings) and identity data (versions)

## Suggestions

1. **Add more data categories** per ECU based on function
2. **Implement data-lists** for bulk reads (get all brake pressures at once)
3. **Add operations** like "ResetFault", "Calibrate", "SoftwareUpdate"
4. **Make data dynamic** - add timestamps, simulate changing values





### PART 2: VEHILE STRUCTURE - create the following entities and logical structure

## Directory Structure

Create mock filesystems in your project:

```
generated-python/server/
├── sovd_api/
│   ├── vehicle_model.py
│   └── mock_filesystems/
│       ├── posix_ecu/          # Communication ECUs
│       │   ├── var/
│       │   │   ├── log/
│       │   │   │   ├── syslog
│       │   │   │   ├── messages
│       │   │   │   └── network.log
│       │   │   └── lib/
│       │   │       └── systemd/
│       │   │           └── coredump/
│       │   ├── etc/
│       │   │   ├── systemd/
│       │   │   └── network/
│       │   └── proc/
│       │       └── meminfo
│       │
│       └── autosar_classic/    # Chassis ECUs
│           ├── fault_memory/
│           │   ├── dtc_snapshot.bin
│           │   └── freeze_frames.dat
│           ├── calibration/
│           │   └── parameters.a2l
│           └── runtime/
│               └── signals.arxml
```

## Data Model Design

Update `vehicle_model.py`:

```python
VEHICLE_DATA = {
    "components": {
        "V2X": {
            "id": "V2X",
            "name": "V2X Communication Module",
            "architecture": "posix",
            "filesystem_root": "mock_filesystems/posix_ecu",
            "bulk_data_categories": ["logs", "coredumps", "configs"],
            "identData": {
                "OS": "Ubuntu 22.04 LTS",
                "Kernel": "5.15.0-91",
                "Arch": "x86_64"
            },
            "log_files": {
                "syslog": "var/log/syslog",
                "network": "var/log/network.log",
                "systemd": "var/log/journal"
            }
        },
        
        "Brakes": {
            "id": "Brakes",
            "name": "Brake Control Module",
            "architecture": "autosar_classic",
            "filesystem_root": "mock_filesystems/autosar_classic",
            "bulk_data_categories": ["fault_memory", "calibration"],
            "identData": {
                "AUTOSAR_Version": "4.2.2",
                "Supplier": "Continental",
                "ECU_Type": "ABS/ESP"
            },
            "fault_memory_location": "fault_memory/dtc_snapshot.bin"
        }
    }
}
```

## Bulk Data Categories by Architecture

POSIX ECUs should expose:
- `logs` - System logs (syslog, dmesg, application logs)
- `coredumps` - Crash dumps from systemd-coredump
- `configs` - Configuration files from /etc
- `diagnostic-traces` - Debug/trace files

AUTOSAR Classic ECUs should expose:
- `fault_memory` - DTC snapshots, freeze frames
- `calibration` - Calibration data (A2L/HEX files)
- `measurement` - Measurement/signal recordings
- `flash_data` - Flash memory dumps

## Implementation Pattern

The bulk-data API in SOVD works like this:

1. **List categories**: `GET /v1/components/V2X/bulk-data` → Returns `["logs", "coredumps", "configs"]`
2. **List items in category**: `GET /v1/components/V2X/bulk-data/logs` → Returns list of available log files
3. **Download specific file**: `GET /v1/components/V2X/bulk-data/logs/syslog-2024-10-01` → Returns file content

For AUTOSAR faults, you'd still use the fault API (`/faults`), but the detailed fault snapshots would be bulk-data:

1. `GET /v1/components/Brakes/faults` → Returns DTC codes
2. `GET /v1/components/Brakes/bulk-data/fault_memory` → Returns available snapshots
3. `GET /v1/components/Brakes/bulk-data/fault_memory/snapshot_20241001_143522` → Download binary snapshot

## Creating Mock Files

Use a script to generate realistic dummy data:

```python
# generate_mock_fs.py
import os
from datetime import datetime

def create_posix_logs():
    os.makedirs("sovd_api/mock_filesystems/posix_ecu/var/log", exist_ok=True)
    
    # Create dummy syslog
    with open("sovd_api/mock_filesystems/posix_ecu/var/log/syslog", "w") as f:
        f.write(f"{datetime.now()} v2x-daemon: Started V2X communication service\n")
        f.write(f"{datetime.now()} kernel: Network interface eth0 up\n")
        f.write(f"{datetime.now()} systemd: v2x.service: Main process exited\n")

def create_autosar_faults():
    os.makedirs("sovd_api/mock_filesystems/autosar_classic/fault_memory", exist_ok=True)
    
    # Create dummy DTC snapshot (binary-like)
    with open("sovd_api/mock_filesystems/autosar_classic/fault_memory/dtc_snapshot.bin", "wb") as f:
        # Mock binary data structure
        f.write(b'\x00\x01\x02\x03')  # Header
        f.write(b'DTC_P0420\x00')      # Fault code
        f.write(b'\x85\x01')            # Status bytes

if __name__ == "__main__":
    create_posix_logs()
    create_autosar_faults()
```

## Questions for Your Design

1. **File realism level**: Do you want actual log format parsing (structured systemd journal vs plain text), or is "looks like a log file" sufficient?

2. **Dynamic vs static**: Should logs accumulate over time as the server runs, or remain static dummy files?

3. **Binary data**: AUTOSAR fault snapshots are typically binary. Do you want:
   - Real binary structures (requires understanding AUTOSAR DTC format)
   - Hex dumps that look binary but are readable
   - JSON representations of what the binary contains

4. **File size**: Real log files can be large. Should mock files be:
   - Minimal (few lines for testing)
   - Realistic size (MBs) to test bulk transfer

The bulk-data implementation is straightforward once you decide on the file structure. The controller just needs to map category → directory → file list → file content.

### Part 2.5

ADAS/Navigation ECUs would likely use a hybrid architecture - mix of embedded Linux (similar to POSIX) for high-level processing and real-time OS for safety-critical functions.

## ADAS/Navigation Architecture

```
mock_filesystems/
├── adas_linux/              # Camera, LIDAR, GOLDBOX
│   ├── opt/
│   │   └── adas/
│   │       ├── models/      # ML models for object detection
│   │       │   ├── yolov8_traffic.onnx
│   │       │   ├── lane_detection_v2.tflite
│   │       │   └── model_metadata.json
│   │       ├── maps/        # HD map data
│   │       │   ├── region_eu_central.bin
│   │       │   └── map_index.db
│   │       └── calibration/
│   │           ├── camera_intrinsics.yaml
│   │           └── lidar_extrinsics.yaml
│   ├── var/
│   │   ├── log/
│   │   │   ├── perception.log
│   │   │   ├── planning.log
│   │   │   └── sensor_fusion.log
│   │   └── recordings/      # Sensor recordings
│   │       ├── scenario_20241001_143000.bag  # ROS bag format
│   │       └── critical_event_20241001.mcap
│   └── tmp/
│       └── diagnostics/
│           └── sensor_health.json
```

## Updated Vehicle Model

```python
VEHICLE_DATA = {
    "components": {
        "Camera": {
            "id": "Camera",
            "name": "Front Camera Unit",
            "architecture": "adas_linux",
            "filesystem_root": "mock_filesystems/adas_linux",
            "bulk_data_categories": ["models", "calibration", "recordings", "logs"],
            "identData": {
                "OS": "Yocto Linux 4.0",
                "Framework": "ROS2 Humble",
                "Resolution": "1920x1080",
                "FPS": 60
            },
            "currentData": {
                "ObjectsDetected": 5,
                "LaneConfidence": 0.95,
                "ProcessingLatency": 12  # milliseconds
            },
            "bulk_data": {
                "models": {
                    "yolov8_traffic.onnx": "opt/adas/models/yolov8_traffic.onnx",
                    "lane_detection_v2.tflite": "opt/adas/models/lane_detection_v2.tflite"
                },
                "logs": {
                    "perception.log": "var/log/perception.log"
                }
            }
        },
        
        "LIDAR": {
            "id": "LIDAR",
            "name": "3D LIDAR Scanner",
            "architecture": "adas_linux", 
            "filesystem_root": "mock_filesystems/adas_linux",
            "bulk_data_categories": ["recordings", "calibration", "logs"],
            "identData": {
                "Manufacturer": "Velodyne",
                "Model": "VLS-128",
                "PointCloudRate": "10Hz"
            },
            "currentData": {
                "PointsPerSecond": 2400000,
                "RangeMax": 200,  # meters
                "ActiveChannels": 128
            },
            "bulk_data": {
                "calibration": {
                    "lidar_extrinsics.yaml": "opt/adas/calibration/lidar_extrinsics.yaml"
                },
                "recordings": {
                    "scenario_20241001_143000.bag": "var/recordings/scenario_20241001_143000.bag"
                }
            }
        },
        
        "GOLDBOX": {
            "id": "GOLDBOX",
            "name": "Central ADAS Processing Unit",
            "architecture": "adas_linux",
            "filesystem_root": "mock_filesystems/adas_linux",
            "bulk_data_categories": ["models", "maps", "recordings", "diagnostics"],
            "identData": {
                "Processor": "NVIDIA Drive AGX Orin",
                "RAM": "64GB",
                "AI_TOPS": "254"
            },
            "currentData": {
                "GPUUtil": 78,  # percent
                "CPUTemp": 65,   # celsius
                "PowerDraw": 120,  # watts
                "ActiveThreads": 24
            },
            "bulk_data": {
                "maps": {
                    "region_eu_central.bin": "opt/adas/maps/region_eu_central.bin"
                },
                "diagnostics": {
                    "sensor_health.json": "tmp/diagnostics/sensor_health.json"
                }
            }
        },
        
        "MAB": {
            "id": "MAB",
            "name": "Multi-Function Actuator Box",
            "architecture": "autosar_adaptive",  # Real-time component
            "filesystem_root": "mock_filesystems/autosar_adaptive",
            "bulk_data_categories": ["fault_memory", "signals", "calibration"],
            "areas": ["ADAS", "Chassis"],
            "identData": {
                "AUTOSAR_Version": "Adaptive R22-11",
                "SafetyLevel": "ASIL-D"
            },
            "currentData": {
                "SteeringTorque": 12.5,
                "BrakePressure": 850,
                "ActuatorTemp": 68
            }
        }
    }
}
```

## Mock File Generator

```python
# generate_mock_fs.py (extended)

def create_adas_files():
    # Create directory structure
    base = "sovd_api/mock_filesystems/adas_linux"
    
    # Models directory
    os.makedirs(f"{base}/opt/adas/models", exist_ok=True)
    
    # Mock ML model metadata
    with open(f"{base}/opt/adas/models/model_metadata.json", "w") as f:
        f.write('''{
  "yolov8_traffic.onnx": {
    "version": "8.0.2",
    "input_size": [640, 640],
    "classes": ["car", "truck", "pedestrian", "bicycle", "traffic_light"],
    "last_updated": "2024-09-15",
    "accuracy": 0.94
  },
  "lane_detection_v2.tflite": {
    "version": "2.1.0",
    "framework": "TensorFlow Lite",
    "latency_ms": 8,
    "accuracy": 0.97
  }
}''')
    
    # Mock perception log
    os.makedirs(f"{base}/var/log", exist_ok=True)
    with open(f"{base}/var/log/perception.log", "w") as f:
        f.write('''2024-10-01 14:30:15 [INFO] Perception pipeline started
2024-10-01 14:30:15 [INFO] Loaded model: yolov8_traffic.onnx
2024-10-01 14:30:16 [INFO] Camera feed active: 60 FPS
2024-10-01 14:30:17 [WARN] Object detection latency spike: 45ms
2024-10-01 14:30:20 [INFO] Detected: 3 cars, 1 pedestrian
2024-10-01 14:30:25 [ERROR] Lane detection confidence low: 0.65
''')
    
    # Mock calibration files
    os.makedirs(f"{base}/opt/adas/calibration", exist_ok=True)
    with open(f"{base}/opt/adas/calibration/camera_intrinsics.yaml", "w") as f:
        f.write('''camera_matrix:
  - [1000.0, 0.0, 960.0]
  - [0.0, 1000.0, 540.0]
  - [0.0, 0.0, 1.0]
distortion_coefficients: [-0.2, 0.05, 0.001, 0.002, 0.0]
resolution: [1920, 1080]
calibration_date: "2024-08-20"
''')
    
    # Mock diagnostic data
    os.makedirs(f"{base}/tmp/diagnostics", exist_ok=True)
    with open(f"{base}/tmp/diagnostics/sensor_health.json", "w") as f:
        f.write('''{
  "timestamp": "2024-10-01T14:30:00Z",
  "sensors": {
    "camera_front": {"status": "healthy", "uptime_hours": 1247},
    "lidar": {"status": "degraded", "error": "reduced_range", "current_range_m": 150},
    "radar_front": {"status": "healthy", "targets_tracked": 8}
  }
}''')

def create_autosar_adaptive():
    base = "sovd_api/mock_filesystems/autosar_adaptive"
    
    # Signals/measurement data
    os.makedirs(f"{base}/runtime", exist_ok=True)
    with open(f"{base}/runtime/signals.arxml", "w") as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR>
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>Signals</SHORT-NAME>
      <ELEMENTS>
        <SIGNAL>
          <SHORT-NAME>SteeringAngle</SHORT-NAME>
          <VALUE>12.5</VALUE>
          <UNIT>degrees</UNIT>
        </SIGNAL>
        <SIGNAL>
          <SHORT-NAME>BrakePressure</SHORT-NAME>
          <VALUE>850</VALUE>
          <UNIT>PSI</UNIT>
        </SIGNAL>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>
''')
```

## Bulk Data Categories Summary

**POSIX Communication ECUs**:
- `logs` - syslog, systemd journal
- `coredumps` - crash dumps
- `configs` - /etc configuration files

**ADAS Linux ECUs**:
- `models` - ML model files (.onnx, .tflite)
- `maps` - HD map databases
- `calibration` - sensor calibration data
- `recordings` - sensor data recordings (ROS bags)
- `logs` - application logs

**AUTOSAR Classic (Chassis)**:
- `fault_memory` - DTC snapshots
- `calibration` - ECU parameters

**AUTOSAR Adaptive (MAB)**:
- `fault_memory` - Enhanced diagnostics
- `signals` - Real-time signal recordings
- `calibration` - Safety-critical parameters

This structure matches real automotive architectures where high-compute perception uses Linux, safety-critical control uses AUTOSAR, and communication modules use standard POSIX.