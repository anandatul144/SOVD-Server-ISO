# SOVD API Server - Mock Vehicle Implementation

## Overview

This project implements a working SOVD (Service-Oriented Vehicle Diagnostics) API server based on the ASAM SOVD specification. It includes a complete mock vehicle architecture with security monitoring applications, realistic ECU structure, and functional REST API endpoints.

## Mock Vehicle Architecture

### Areas (Security Zones)
- **Communication Zone**: External connectivity and network gateway
- **ADAS Zone**: Advanced driver assistance and sensor fusion
- **Chassis Zone**: Core vehicle control and actuation

### Components (ECUs)

**Communication Zone:**
- V2X Gateway (external gateway, runs IDSReporter, SOVD Server)
- Network Switch (zone gateway between Communication/ADAS, runs Suricata NIDS)
- ECU1, ECU2, Ubuntu (telematics)

**ADAS Zone:**
- Camera (perception)
- LIDAR (3D scanning)
- GOLDBOX (central compute, runs IDS Manager, OSSEC HIDS)
- MAB (shared with Chassis, runs CAN IDS)

**Chassis Zone:**
- Wheels, Brakes, Accelerator, Gearbox
- MAB (multi-function actuator, shared gateway)

### Security Applications

The vehicle implements a distributed intrusion detection system:

- **IDSReporter** (V2X): Aggregates alerts from all zone gateways
- **NIDS_Suricata** (Switch): Network traffic analysis
- **IDSManager** (GOLDBOX): Alert correlation and threat analysis
- **HIDS_OSSEC** (GOLDBOX): Host-based integrity monitoring
- **CANIDS** (MAB): CAN bus anomaly detection

Each gateway ECU runs a local IDS that reports to the central IDSReporter.

## Prerequisites

```bash
# Install Node.js tools
sudo npm install -g @apidevtools/swagger-cli@4.0.4
sudo npm install -g @openapitools/openapi-generator-cli

# Install Python dependencies
pip install pyyaml
```

## ASAM SOVD Spec Issues

The official spec requires fixes before generation:

1. External GitHub schema references (404 errors)
2. OpenAPI 3.1.0 (Connexion only supports 3.0.x)
3. Custom JSON schema dialect
4. Multi-file structure with complex references

## Required Spec Modifications

### 1. Fix `commons/types.yaml` (line ~35)

Replace:
```yaml
OpenApiSchema:
  $ref: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml#/$defs/schema
```

With:
```yaml
OpenApiSchema:
  type: object
  additionalProperties: true
```

### 2. Fix `capability-description/capability-description.yaml` (line ~56)

Replace:
```yaml
schema:
  $ref: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml
```

With:
```yaml
schema:
  type: object
  additionalProperties: true
```

### 3. Fix `sovd-api.yaml`

Delete line 2:
```yaml
jsonSchemaDialect: https://asam.net/standards/diagnostics/sovd/v1.1/dialect
```

Change line 1:
```yaml
openapi: 3.0.3  # Changed from 3.1.0
```

## Generation Process

### Step 1: Bundle the Specification

```bash
swagger-cli bundle sovd-api.yaml --outfile sovd-bundled.yaml --type yaml --dereference
```

This resolves all `$ref` references into a single file.

### Step 2: Generate Python Flask Server

```bash
openapi-generator-cli generate \
  -i sovd-bundled.yaml \
  -g python-flask \
  -o ./generated-python/server \
  --skip-validate-spec \
  --additional-properties=packageName=sovd_api
```

### Step 3: Fix Bulk-Data Validation

The generated `sovd_api/openapi/openapi.yaml` contains restrictive enum values for bulk-data categories. Remove all 6 instances of:

```yaml
enum:
  - maps
  - pois
  - logs
```

Search for these blocks and delete them entirely, leaving just `type: string`.

### Step 4: Install and Run

```bash
cd generated-python/server
pip install -r requirements.txt
python -m sovd_api
```

Server runs on `http://localhost:8080` with `/v1/` base path.

## Mock Filesystem Structure

Located at project root: `Target-mock-FS/`

```
Target-mock-FS/
├── adas_linux
│   ├── camera
│   ├── goldbox
│   └── lidar
├── autosar_adaptive
│   └── mab
├── autosar_classic
│   ├── accelerator
│   ├── brakes
│   ├── gearbox
│   └── wheels
├── mock_filesystems
│   ├── adas_linux
│   ├── autosar_adaptive
│   ├── autosar_classic
│   └── posix_comms
└── posix_comms
    ├── ecu1
    ├── ecu2
    ├── switch
    ├── ubuntu
    └── v2x

```
Complete FS tree availale here : <Project root>/mock-fs-full-free.txt
Files are empty placeholders created with `touch`. Add content as needed.

## Implementation Details

### Vehicle Model

`sovd_api/vehicle_model.py` defines the complete structure:

```python
VEHICLE_DATA = {
    "areas": {...},       # 3 areas with component mappings
    "components": {...},  # 13 ECUs with properties
    "apps": {...}        # 14 applications with data/bulk-data
}
```

Helper functions:
- `get_component(component_id)` - Retrieve component by ID
- `get_app(app_id)` - Retrieve app by ID
- `get_area(area_id)` - Retrieve area by ID
- `get_components_in_area(area_id)` - List area's components
- `get_apps_for_component(component_id)` - List component's apps

### Implemented Controllers

**discovery_controller.py:**
- List areas, components, apps
- Component-to-app relationships
- Area-to-component relationships

**data_retrieval_controller.py:**
- Read component identData/currentData
- Read app runtime data
- List all data resources

**bulk_data_controller.py:**
- List bulk-data categories per app
- List files in each category
- Download specific files

## API Examples

```bash
# Discovery
curl http://localhost:8080/v1/areas
curl http://localhost:8080/v1/components
curl http://localhost:8080/v1/apps

# Relationships
curl http://localhost:8080/v1/areas/Communication/related-components
curl http://localhost:8080/v1/components/V2X/related-apps

# Component Data
curl http://localhost:8080/v1/components/V2X/data
curl http://localhost:8080/v1/components/V2X/data/CPULoad

# App Data  
curl http://localhost:8080/v1/apps/IDSReporter/data/alertCount
curl http://localhost:8080/v1/apps/NIDS_Suricata/data/packetsProcessed

# Bulk Data (Files)
curl http://localhost:8080/v1/apps/IDSReporter/bulk-data
curl http://localhost:8080/v1/apps/IDSReporter/bulk-data/ids_alerts
curl http://localhost:8080/v1/apps/IDSReporter/bulk-data/ids_alerts/alert_20241001_143000.json
curl http://localhost:8080/v1/apps/NIDS_Suricata/bulk-data/suricata_rules
curl http://localhost:8080/v1/apps/IDSManager/bulk-data/correlation_rules
```

## Project Structure

```
generated-python/server/
├── sovd_api/
│   ├── controllers/           # 14 endpoint controllers
│   ├── models/               # 70+ data model classes
│   ├── openapi/              # OpenAPI specification
│   ├── vehicle_model.py      # Mock vehicle structure
│   └── __main__.py           # Server entry point
├── requirements.txt
└── setup.py
```

## Key Design Decisions

1. **Mock filesystem outside package**: `Target-mock-FS/` at project root, symlinked from `sovd_api/mock_filesystems`

2. **Removed bulk-data enum**: Original spec had example categories. Removed to support real IDS categories (ids_alerts, suricata_rules, etc.)

3. **No authentication**: Focus on functional implementation, not security

4. **Stub implementations**: Controllers return mock data from vehicle_model.py

5. **Shared components**: MAB appears in both ADAS and Chassis areas (realistic gateway design)

## Extending the Implementation

### Add Realistic File Content

```bash
# Example: Add IDS alert
cat > Target-mock-FS/posix_comms/v2x/opt/ids_reporter/alerts/alert_20241001_143000.json << 'EOF'
{
  "timestamp": "2024-10-01T14:30:00Z",
  "source": "NIDS_Suricata",
  "severity": "high",
  "alert": "Possible port scan detected",
  "source_ip": "192.168.1.100"
}
EOF
```

### Implement Operations

Edit `sovd_api/controllers/operations_control_controller.py`:

```python
def entity_collection_entity_id_operations_operation_id_executions_post(
    entity_collection, entity_id, operation_id, body=None
):
    """Execute operation"""
    import uuid
    execution_id = str(uuid.uuid4())
    
    # Implement operation logic
    return {
        "id": execution_id,
        "status": "running"
    }, 202
```

### Add Fault Handling

Edit `sovd_api/controllers/fault_handling_controller.py`:

```python
def get_faults(entity_collection, entity_id, status=None, severity=None):
    """Return DTCs"""
    from sovd_api.vehicle_model import get_component
    
    component = get_component(entity_id)
    if component and "faults" in component:
        return {"items": component["faults"]}, 200
    
    return {"items": []}, 200
```

## Containerization

**Dockerfile** (in `generated-python/server/`):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sovd_api/ ./sovd_api/

# Mount point for vehicle filesystem
VOLUME /vehicle-fs

ENV MOCK_FS_BASE=/vehicle-fs

EXPOSE 8080
CMD ["python", "-m", "sovd_api"]
```

Build and run:
```bash
docker build -t sovd-server .
docker run -p 8080:8080 sovd-server
```

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vehicle-fs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sovd-server
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: sovd-server
        image: sovd-server:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: vehicle-fs
          mountPath: /vehicle-fs
      volumes:
      - name: vehicle-fs
        persistentVolumeClaim:
          claimName: vehicle-fs-pvc

## Version Control

**.gitignore:**
```
generated-python/
.SOVDServer/
*.pyc
__pycache__/
*.egg-info/
```

**Commit source files only:**
```bash
git add commons/ capability-description/ sovd-api.yaml sovd-bundled.yaml
git add Target-mock-FS/
git add README.md .gitignore
git commit -m "Working SOVD server with mock vehicle and IDS apps"
```

## Troubleshooting

**All endpoints return 404:**  
Add `/v1/` prefix to URLs. The spec defines `servers: - url: https://sovd.server/v1`

**Bulk-data validation errors:**  
Ensure enum blocks are removed from `sovd_api/openapi/openapi.yaml`

**Empty controllers/models:**  
Check that `sovd-bundled.yaml` contains actual operation definitions (not empty `{}`). Rebundle if needed.

**Import errors for vehicle_model:**  
Verify `sovd_api/vehicle_model.py` exists and MOCK_FS_BASE path is correct

## Next Steps

1. Add realistic content to mock files (alerts, logs, rules)
2. Implement remaining controllers (faults, operations, configurations)
3. Add dynamic data generation (sensor values changing over time)
4. Integrate with NLP interface for natural language queries
5. Build actual vehicle simulator backend

## Quick Reference

```bash
# Complete generation workflow
swagger-cli bundle sovd-api.yaml --outfile sovd-bundled.yaml --type yaml --dereference
openapi-generator-cli generate -i sovd-bundled.yaml -g python-flask -o ./generated-python/server --skip-validate-spec
cd generated-python/server
pip install -r requirements.txt
python -m sovd_api

# Test
curl http://localhost:8080/v1/components
curl http://localhost:8080/v1/apps/IDSReporter/bulk-data/ids_alerts
```