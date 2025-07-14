import sys
import os

print("--- sys.path at script start ---")
for p in sys.path:
    print(p)

print("\n--- PYTHONPATH environment variable ---")
print(os.environ.get('PYTHONPATH'))

print("\n--- Attempting import of ai_model ---")
try:
    import ai_model
    print(f"Successfully imported ai_model from: {ai_model.__file__}")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {e}")

print("\n--- Attempting import of get_settings from backend-api structure ---")
try:
    # This mimics the failing import chain from app/utils/config.py
    # If this fails, it's consistent with the uvicorn error
    from app.main import app # This would trigger the whole import chain
    print("Successfully imported app from app.main")
except ImportError as e:
    print(f"ImportError during app import: {e}")

print("\n--- Script finished ---")