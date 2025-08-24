#!/usr/bin/env python3
"""
Simple test script to debug Flask app import issues
"""

print("Starting import test...")

try:
  print("1. Importing Flask...")
  from flask import Flask
  print("   ✓ Flask imported successfully")

  print("2. Importing app package...")
  import app
  print("   ✓ App package imported successfully")

  print("3. Importing create_app function...")
  from app import create_app
  print("   ✓ create_app imported successfully")

  print("4. Creating Flask app instance...")
  flask_app = create_app()
  print("   ✓ Flask app created successfully")

  print("\nAll tests passed! ✅")

except Exception as e:
  print(f"\n❌ Error: {e}")
  import traceback
  traceback.print_exc()
