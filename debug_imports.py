import sys
import os

print("Python Path:")
for path in sys.path:
    print(path)

print("\nTrying to find rtaspi package:")
try:
    import rtaspi
    print(f"rtaspi package found at: {rtaspi.__file__}")
    try:
        import rtaspi.core
        print(f"rtaspi.core found at: {rtaspi.core.__file__}")
    except ImportError as e:
        print(f"Failed to import rtaspi.core: {e}")
except ImportError as e:
    print(f"Failed to import rtaspi: {e}")

print("\nChecking if src/rtaspi/core exists:")
core_path = os.path.join(os.getcwd(), 'src', 'rtaspi', 'core')
print(f"Looking for: {core_path}")
print(f"Directory exists: {os.path.exists(core_path)}")
if os.path.exists(core_path):
    print("Contents:")
    print(os.listdir(core_path))
