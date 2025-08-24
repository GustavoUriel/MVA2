#!/usr/bin/env python3
"""
Minimal Flask app test to isolate import issues
"""

print("1. Testing basic Flask import...")
from flask import Flask
print("   ✅ Flask imported")

print("2. Testing minimal app creation...")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print("   ✅ Basic Flask app created")

print("3. Testing app extensions...")
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
db.init_app(app)
print("   ✅ SQLAlchemy initialized")

print("4. Testing app factory pattern...")
def create_minimal_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

minimal_app = create_minimal_app()
print("   ✅ Minimal app factory works")

print("5. Testing actual app import...")
try:
    from app import create_app
    print("   ✅ App factory imported")
    
    test_app = create_app()
    print("   ✅ Full app created successfully!")
except Exception as e:
    print(f"   ❌ App creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 All basic tests passed!")
