# fix_openapi.py
import yaml
import sys
from pathlib import Path

def fix_examples(data):
    """Convert schema-level examples to content-level examples"""
    if isinstance(data, dict):
        # Check if this is a schema with examples
        if 'schema' in data and 'examples' in data['schema']:
            # Move examples up one level
            examples_value = data['schema'].pop('examples')
            if 'content' in data:
                for content_type in data['content'].values():
                    if 'schema' in content_type:
                        content_type['examples'] = examples_value
        
        # Recursively process all dictionary values
        for key, value in data.items():
            data[key] = fix_examples(value)
    
    elif isinstance(data, list):
        return [fix_examples(item) for item in data]
    
    return data

# Fix faults/responses.yaml
file_path = Path('faults/responses.yaml')
with open(file_path, 'r') as f:
    data = yaml.safe_load(f)

data = fix_examples(data)

with open(file_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {file_path}")

# Repeat for data/responses.yaml
file_path = Path('data/responses.yaml')
with open(file_path, 'r') as f:
    data = yaml.safe_load(f)

data = fix_examples(data)

with open(file_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {file_path}")