#!/usr/bin/env python3
import os
import sys
import subprocess
import importlib
from pathlib import Path

def setup_directories():
    """Create correct and error directories if they don't exist."""
    Path('correct').mkdir(exist_ok=True)
    Path('error').mkdir(exist_ok=True)

def check_rtaspi_installed():
    """Check if rtaspi package is installed."""
    try:
        import rtaspi
        return True
    except ImportError:
        return False

def install_rtaspi():
    """Install rtaspi package in development mode."""
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-e', '.'],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install rtaspi: {e.stderr}")
        return False

def find_python_files(directory):
    """Recursively find all .py files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    return python_files

def run_example(python_file):
    """Run a Python file and capture its output."""
    try:
        # Run the Python file and capture output/errors
        result = subprocess.run(
            [sys.executable, python_file],
            capture_output=True,
            text=True,
            timeout=30  # Set timeout to 30 seconds
        )
        
        # Get the base filename without path
        base_name = os.path.basename(python_file)
        
        if result.returncode == 0:
            # Success case - write to correct/
            output_file = os.path.join('correct', f"{base_name}.log")
            output_content = f"=== Successfully ran {base_name} ===\n\nSTDOUT:\n{result.stdout}\n"
            if result.stderr:
                output_content += f"\nSTDERR:\n{result.stderr}"
        else:
            # Error case - write to error/
            output_file = os.path.join('error', f"{base_name}.log")
            output_content = f"=== Error running {base_name} ===\n\nExit code: {result.returncode}\n"
            if result.stdout:
                output_content += f"\nSTDOUT:\n{result.stdout}"
            output_content += f"\nSTDERR:\n{result.stderr}"
        
        # Write the output to appropriate file
        with open(output_file, 'w') as f:
            f.write(output_content)
            
        return result.returncode == 0
            
    except subprocess.TimeoutExpired:
        # Handle timeout case
        output_file = os.path.join('error', f"{os.path.basename(python_file)}.log")
        with open(output_file, 'w') as f:
            f.write(f"=== Timeout running {os.path.basename(python_file)} ===\nExecution exceeded 30 seconds timeout.")
        return False
    except Exception as e:
        # Handle any other exceptions
        output_file = os.path.join('error', f"{os.path.basename(python_file)}.log")
        with open(output_file, 'w') as f:
            f.write(f"=== Error running {os.path.basename(python_file)} ===\nException: {str(e)}")
        return False

def main():
    # Setup output directories
    setup_directories()
    
    # Check if rtaspi is installed
    if not check_rtaspi_installed():
        print("rtaspi package not found. Installing in development mode...")
        if not install_rtaspi():
            print("Failed to install rtaspi package. Examples may not work correctly.")
    
    # Find all Python files in examples/
    python_files = find_python_files('examples')
    
    # Statistics
    total = len(python_files)
    successful = 0
    failed = 0
    
    print(f"Found {total} Python files to run\n")
    print("Note: Some examples may require additional services to be running (e.g. web server, MQTT broker)")
    print("      Check the error logs for specific requirements.\n")
    
    # Run each example
    for python_file in python_files:
        print(f"Running {python_file}...", end=' ')
        if run_example(python_file):
            print("SUCCESS")
            successful += 1
        else:
            print("FAILED")
            failed += 1
    
    # Print summary
    print(f"\nExecution complete!")
    print(f"Total files: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nCheck 'correct/' and 'error/' directories for detailed logs.")
    
    if failed > 0:
        print("\nNote: Failures may be due to:")
        print("1. Missing dependencies")
        print("2. Required services not running (web server, MQTT broker, etc.)")
        print("3. Hardware requirements (camera, microphone, etc.)")
        print("4. Configuration files not set up")
        print("\nCheck the error logs for specific details about each failure.")

if __name__ == '__main__':
    main()
