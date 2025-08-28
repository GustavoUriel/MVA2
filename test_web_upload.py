#!/usr/bin/env python3
"""
Test the web upload process step by step
"""

import json
import requests
import sys
import os
sys.path.insert(0, os.path.abspath('.'))


def test_web_upload():
  """Test the web upload process"""

  print("=== Testing Web Upload Process ===")

  base_url = "http://127.0.0.1:5000"

  # First, let's test the analyze endpoint
  try:
    print("1. Testing file analysis...")

    with open('instance/bracken.csv', 'rb') as f:
      files = {'file': ('bracken.csv', f, 'text/csv')}
      response = requests.post(
          f"{base_url}/api/v1/uploads/analyze", files=files)

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.text[:500]}...")
    if response.status_code == 200:
      try:
        result = response.json()
        print(f"Analysis result:")
        print(f"  File type detected: {result.get('file_type', 'unknown')}")
        if 'sheets' in result:
          for i, sheet in enumerate(result['sheets']):
            print(f"  Sheet {i+1}: {sheet.get('sheet_name', 'unnamed')}")
            print(f"    Rows: {sheet.get('rows', 0)}")
            print(f"    Columns: {sheet.get('columns', 0)}")
            print(f"    Data type: {sheet.get('data_type', 'unknown')}")
            print(f"    Sample columns: {sheet.get('sample_columns', [])[:5]}")
      except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    else:
      print(f"Error: {response.text}")

  except requests.exceptions.ConnectionError:
    print("Error: Flask app is not running or not accessible")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == '__main__':
  test_web_upload()
