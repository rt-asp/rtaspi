import os
import sys
import pytest
from pathlib import Path

def pytest_configure(config):
    """Configure pytest before running tests."""
    # Get absolute paths
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    src_dir = project_root / 'src'
    
    print("\nDirectory structure:")
    print(f"Current dir: {current_dir}")
    print(f"Project root: {project_root}")
    print(f"Src dir: {src_dir}")
    
    # Verify src/rtaspi exists
    rtaspi_dir = src_dir / 'rtaspi'
    if not rtaspi_dir.exists():
        raise RuntimeError(f"rtaspi package directory not found at {rtaspi_dir}")
    
    # Clear sys.path and add our paths
    sys.path.clear()
    sys.path.extend([
        str(src_dir),
        str(project_root / 'venv/lib/python3.12/site-packages'),
        '/home/tom/miniconda3/lib/python3.12',
        '/home/tom/miniconda3/lib/python3.12/lib-dynload'
    ])
    
    # Print Python path
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")
    

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup any test environment variables or configurations."""
    pass
