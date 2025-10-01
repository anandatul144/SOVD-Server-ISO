# SOVD API Server Generation Guide

## Overview

This guide documents the complete process of generating a working Python Flask server from the ASAM SOVD (Service-Oriented Vehicle Diagnostics) OpenAPI specification.

## Prerequisites

```bash
# Install Node.js tools
sudo npm install -g @apidevtools/swagger-cli@4.0.4
sudo npm install -g @openapitools/openapi-generator-cli

# Install Python dependencies
pip install pyyaml
```

## The Problem

The ASAM SOVD specification has several issues preventing direct code generation:

1. References external GitHub schemas that return 404
2. Uses OpenAPI 3.1.0 (Connexion framework only supports 3.0.x)
3. Uses custom JSON schema dialect not supported by standard tools
4. Multi-file structure with complex `$ref` references

## Solution: 4 Required Fixes

### 1. Fix `commons/types.yaml`

Find line ~35 and replace:

```yaml
# BEFORE
OpenApiSchema:
  $ref: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml#/$defs/schema
  description: >-
    The schema definition of the response.

# AFTER
OpenApiSchema:
  type: object
  additionalProperties: true
  description: >-
    The schema definition of the response.
```

### 2. Fix `capability-description/capability-description.yaml`

Find line ~56 and replace:

```yaml
# BEFORE
schema:
  $ref: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml

# AFTER
schema:
  type: object
  additionalProperties: true
```

### 3. Fix `sovd-api.yaml` - Remove Custom Dialect

Delete line 2:

```yaml
# DELETE THIS LINE
jsonSchemaDialect: https://asam.net/standards/diagnostics/sovd/v1.1/dialect
```

### 4. Fix `sovd-api.yaml` - Downgrade OpenAPI Version

Change line 1:

```yaml
# BEFORE
openapi: 3.1.0

# AFTER
openapi: 3.0.3
```

## Generation Process

### Step 1: Bundle the Specification

```bash
swagger-cli bundle sovd-api.yaml \
  --outfile sovd-bundled.yaml \
  --type yaml \
  --dereference
```

This combines all separate YAML files into a single file with all `$ref` references resolved.

### Step 2: Generate Python Flask Server

```bash
openapi-generator-cli generate \
  -i sovd-bundled.yaml \
  -g python-flask \
  -o ./generated-python/server \
  --skip-validate-spec \
  --additional-properties=packageName=sovd_api
```

### Step 3: Install and Run

```bash
cd generated-python/server
pip install -r requirements.txt
python -m sovd_api
```

The server starts on `http://localhost:8080`

## Testing the Server

All endpoints require the `/v1/` prefix:

```bash
# Discovery - List components
curl http://localhost:8080/v1/components

# Data retrieval - Get data categories
curl http://localhost:8080/v1/components/PowerSteering/data-categories

# Fault handling - Get DTCs
curl http://localhost:8080/v1/components/EngineControl/faults

# Updates - List available updates
curl http://localhost:8080/v1/updates

# Operations - Execute operation
curl -X POST http://localhost:8080/v1/components/BrakeSystem/operations/BleedBrakes/executions \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'
```

## Generated Structure

```
generated-python/server/
├── sovd_api/
│   ├── controllers/          # 14 endpoint controllers
│   │   ├── data_retrieval_controller.py
│   │   ├── fault_handling_controller.py
│   │   ├── operations_control_controller.py
│   │   └── ... (11 more)
│   ├── models/              # 70+ data model classes
│   ├── openapi/             # OpenAPI spec
│   └── __main__.py          # Server entry point
├── requirements.txt
└── setup.py
```

## Implementing Business Logic

The generated controllers return stub responses (`"do some magic!"`). Edit controller files to implement real logic:

**Example: `sovd_api/controllers/fault_handling_controller.py`**

```python
def get_faults(entity_collection, entity_id, status=None, severity=None, scope=None):
    """Return fault/DTC list for an entity"""
    
    # Your implementation here
    faults = [
        {
            "code": "P0420",
            "fault_name": "Catalyst System Efficiency Below Threshold",
            "severity": 2,
            "status": {"aggregatedStatus": "active"}
        }
    ]
    
    return {"items": faults}, 200
```

## Git Repository Management

**.gitignore:**
```
generated-python/
.SOVDServer/
*.pyc
__pycache__/
*.egg-info/
```

## Troubleshooting

**Issue: "unable to read" GitHub schema error**
- Solution: Ensure all 4 fixes above are applied

**Issue: All endpoints return 404**
- Solution: Add `/v1/` prefix to URLs
- Server base path is configured as `/v1` in the spec

**Issue: Empty controllers/models folders**
- Solution: Check bundled spec has actual operation definitions, not empty `{}`
- Rebundle after applying fixes

**Issue: Connexion validation error about OpenAPI version**
- Solution: Ensure `sovd-api.yaml` line 1 is `openapi: 3.0.3`

## Key Learnings

1. **Bundling is critical**: Multi-file OpenAPI specs must be bundled before generation
2. **External references break generation**: Replace with inline definitions
3. **Version compatibility matters**: Match OpenAPI version to generator framework
4. **Base paths are preserved**: The spec's `servers.url` becomes the base path
5. **Generated code is disposable**: Never commit generated code to git

## Next Steps

1. Implement business logic in controller methods
2. Add database integration for persistent data
3. Implement authentication/authorization
4. Add real vehicle communication protocols
5. Write tests for implemented endpoints

## Commands Quick Reference

```bash
# Bundle spec
swagger-cli bundle sovd-api.yaml --outfile sovd-bundled.yaml --type yaml --dereference

# Generate server
openapi-generator-cli generate -i sovd-bundled.yaml -g python-flask -o ./generated-python/server --skip-validate-spec

# Run server
cd generated-python/server && pip install -r requirements.txt && python -m sovd_api

# Test endpoint
curl http://localhost:8080/v1/components
```