#!/usr/bin/env python3

import os
import sys
import glob
from lxml import etree
from pathlib import Path

def split_wsdl(input_wsdl_path, output_directory):
    """Extract inline XSD schemas from WSDL and save them as separate files."""
    
    # Create output directory
    os.makedirs(output_directory, exist_ok=True)
    
    # Parse the WSDL file
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        wsdl_tree = etree.parse(input_wsdl_path, parser)
        wsdl_root = wsdl_tree.getroot()
    except Exception as e:
        print(f"Error parsing WSDL file {input_wsdl_path}: {e}")
        return False
    
    # Define namespaces
    namespaces = {
        'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
        'xsd': 'http://www.w3.org/2001/XMLSchema'
    }
    
    # Find the types element
    types_element = wsdl_root.find('.//wsdl:types', namespaces)
    
    if types_element is None:
        print(f"Warning: No types element found in {input_wsdl_path}")
        return True
    
    # Extract all xsd:schema elements
    schemas = types_element.findall('.//xsd:schema', namespaces)
    
    if not schemas:
        print(f"Warning: No schemas found in types element of {input_wsdl_path}")
        return True
    
    schema_index = 0
    for schema in schemas:
        target_namespace = schema.get('targetNamespace', f'schema_{schema_index}')
        
        # Sanitize filename
        filename = sanitize_filename(target_namespace)
        output_path = os.path.join(output_directory, f'{filename}.xsd')
        
        # Write schema to file
        try:
            with open(output_path, 'wb') as f:
                f.write(etree.tostring(
                    schema,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding='UTF-8'
                ))
            print(f"✓ Extracted XSD: {output_path}")
        except Exception as e:
            print(f"✗ Error writing {output_path}: {e}")
            return False
        
        schema_index += 1
    
    # Save the WSDL file
    output_wsdl_path = os.path.join(
        output_directory,
        os.path.basename(input_wsdl_path)
    )
    
    try:
        wsdl_tree.write(
            output_wsdl_path,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        )
        print(f"✓ Saved WSDL: {output_wsdl_path}")
    except Exception as e:
        print(f"✗ Error writing WSDL file {output_wsdl_path}: {e}")
        return False
    
    return True

def sanitize_filename(name):
    """Convert a namespace to a valid filename."""
    import re
    name = name.replace('http://', '').replace('https://', '').replace('://', '_')
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name[:50]  # Limit length

def process_wsdl_files(input_directory, output_directory):
    """Process all WSDL files in a directory."""
    wsdl_files = glob.glob(os.path.join(input_directory, '**', '*.wsdl'), recursive=True)
    
    if not wsdl_files:
        print(f"No WSDL files found in {input_directory}")
        return False
    
    print(f"Found {len(wsdl_files)} WSDL file(s) to process\n")
    
    success = True
    for wsdl_file in wsdl_files:
        print(f"Processing: {wsdl_file}")
        if not split_wsdl(wsdl_file, output_directory):
            success = False
        print()
    
    return success

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python wsdl_splitter.py <input.wsdl|input_directory> [output_directory]")
        print("\nExamples:")
        print("  python wsdl_splitter.py service.wsdl")
        print("  python wsdl_splitter.py service.wsdl ./output/")
        print("  python wsdl_splitter.py . ./output/")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './wsdl-output'
    
    # Check if input is a directory or file
    if os.path.isdir(input_path):
        success = process_wsdl_files(input_path, output_dir)
    else:
        success = split_wsdl(input_path, output_dir)
    
    sys.exit(0 if success else 1)
