# SOVD API Server Generation Guide

## Overview

This document explains how to generate a working Python Flask server from the ASAM SOVD (Service-Oriented Vehicle Diagnostics) OpenAPI specification.

## Prerequisites

Install the required tools and libraries:

```bash
# Node.js tools
sudo npm install -g @apidevtools/swagger-cli@4.0.4
sudo npm install -g @openapitools/openapi-generator-cli

# Python dependencies
pip install pyyaml
```

## Common Issues with the ASAM SOVD Spec

The official SOVD spec has several quirks that complicate code generation:

- References to external GitHub schemas that may be unavailable
- Uses OpenAPI 3.1.0, but most Python frameworks (like Connexion) only support 3.0.x
- Custom JSON schema dialects not supported by standard tools
- Multi-file structure with complex `$ref` links

## Required Fixes

Before generating code, make these changes:

1. **Edit `commons/types.yaml`**  
   Replace the external `$ref` with a local schema:
   ```yaml
   OpenApiSchema:
     type: object
     additionalProperties: true
     description: The schema definition of the response.
   ```

2. **Edit `capability-description/capability-description.yaml`**  
   Change the schema reference to:
   ```yaml
   schema:
     type: object
     additionalProperties: true
   ```

3. **Edit `sovd-api.yaml`**  
   Remove the custom dialect line:
   ```yaml
   # Delete this line
   jsonSchemaDialect: https://asam.net/standards/diagnostics/sovd/v1.1/dialect
   ```
   Change the OpenAPI version to 3.0.3:
   ```yaml
   openapi: 3.0.3
   ```

## Step-by-Step Process

### 1. Bundle the Specification

Combine all YAML files into one, resolving `$ref` links:

```bash
swagger-cli bundle sovd-api.yaml --outfile sovd-bundled.yaml --type yaml --dereference
```

### 2. Generate the Python Flask Server

Run the generator:

```bash
openapi-generator-cli generate \
  -i sovd-bundled.yaml \
  -g python-flask \
  -o ./generated-python/server \
  --skip-validate-spec \
  --additional-properties=packageName=sovd_api
```

### 3. Install and Start the Server

```bash
cd generated-python/server
pip install -r requirements.txt
python -m sovd_api
```

The server will be available at `http://localhost:8080`.

## Testing Endpoints

All endpoints use the `/v1/` prefix. Example requests:

```bash
curl http://localhost:8080/v1/components
curl http://localhost:8080/v1/components/PowerSteering/data-categories
curl http://localhost:8080/v1/components/EngineControl/faults
curl http://localhost:8080/v1/updates
curl -X POST http://localhost:8080/v1/components/BrakeSystem/operations/BleedBrakes/executions \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'
```

## Project Structure

```
generated-python/server/
├── sovd_api/
│   ├── controllers/
│   ├── models/
│   ├── openapi/
│   └── __main__.py
├── requirements.txt
└── setup.py
```

- Controllers: Endpoint logic (edit these to implement real functionality)
- Models: Data classes
- openapi/: Spec files
- __main__.py: Server entry point

## Implementing Logic

Controller methods are stubs by default. Add your business logic as needed.

Example (`sovd_api/controllers/fault_handling_controller.py`):

```python
def get_faults(entity_collection, entity_id, status=None, severity=None, scope=None):
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

## Version Control

Add generated code and build artifacts to `.gitignore`:

```
generated-python/
.SOVDServer/
*.pyc
__pycache__/
*.egg-info/
```

## Troubleshooting

- **404 errors:** Add `/v1/` to your URLs.
- **Empty controllers/models:** Make sure your bundled spec defines actual operations.
- **OpenAPI version errors:** Confirm the spec uses `openapi: 3.0.3`.

## Next Steps

- Implement real logic in controllers
- Add database integration
- Set up authentication/authorization
- Integrate with vehicle protocols
- Write endpoint tests

## Quick Reference

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

## Containerization

To run the server in Docker, create a `Dockerfile` in `generated-python/server/`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sovd_api/ ./sovd_api/
EXPOSE 8080
CMD ["python", "-m", "sovd_api"]
```

Build and run:

```bash
docker build -t sovd-server .
docker run -p 8080:8080 sovd-server
```

For production, use Gunicorn and expose the Flask app in `__main__.py`:

```python
app = connexionapp.app
```

---

Let me know if you want this saved to your README or need further edits!