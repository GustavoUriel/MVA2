#!/usr/bin/env python3
"""
Comprehensive test script to identify all Flask app issues
"""

import sys
import traceback


def test_step(step_name, test_func):
  """Helper to test individual steps"""
  try:
    print(f"Testing {step_name}...")
    test_func()
    print(f"  ✅ {step_name} - SUCCESS")
    return True
  except Exception as e:
    print(f"  ❌ {step_name} - FAILED: {e}")
    traceback.print_exc()
    return False


def test_flask_import():
  """Test basic Flask import"""
  from flask import Flask


def test_models_import():
  """Test models import"""
  from app.models import user, patient, analysis, taxonomy


def test_blueprints_import():
  """Test blueprint imports"""
  from app.routes.main import main_bp
  from app.auth import bp as auth_bp
  from app.data import bp as data_bp
  from app.analysis import bp as analysis_bp
  from app.api import bp as api_bp


def test_app_creation():
  """Test Flask app creation"""
  from app import create_app
  app = create_app()


def main():
  """Run all tests"""
  print("=== Flask Application Comprehensive Test ===\n")

  tests = [
      ("Flask Import", test_flask_import),
      ("Models Import", test_models_import),
      ("Blueprints Import", test_blueprints_import),
      ("App Creation", test_app_creation),
  ]

  passed = 0
  total = len(tests)

  for test_name, test_func in tests:
    if test_step(test_name, test_func):
      passed += 1
    print()

  print(f"=== Results: {passed}/{total} tests passed ===")

  if passed == total:
    print("🎉 All tests passed! Flask app is ready to run.")
  else:
    print("⚠️  Some tests failed. Check the errors above.")
    sys.exit(1)


if __name__ == "__main__":
  main()
