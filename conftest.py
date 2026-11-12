# Copyright 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

"""Root conftest.py to ensure FFIAM build plugin is available when running pytest from main directory."""

import sys
import pytest
from pathlib import Path

# Add FFIAM tests to Python path so the build plugin can be imported
ffiam_tests_path = Path(__file__).parent / "independent" / "ffiam" / "pyffiam" / "tests"
if ffiam_tests_path.exists():
    sys.path.insert(0, str(ffiam_tests_path))

# Import the FFIAM build plugin to ensure it runs when pytest starts from main directory
def pytest_sessionstart(session):
    """Ensure FFIAM library is built when running pytest from main directory."""
    try:
        from pytest_ffiam_build import build_ffiam_library
        build_ffiam_library()
    except ImportError:
        # If the build plugin can't be imported, that's ok - it means we're not in a FFIAM environment
        pass
    except Exception as e:
        # Log any other errors but don't crash
        print(f"\nFFIAM build plugin error: {e}")
        print("FFIAM tests will be skipped if dependencies are not available.\n")
        session._ffiam_build_error = str(e)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle FFIAM test skipping gracefully."""
    # Check if FFIAM tests should be skipped
    ffiam_tests = [item for item in items if 'ffiam' in str(item.fspath).lower()]
    
    if not ffiam_tests:
        return
    
    # Check if we have the necessary dependencies
    import subprocess
    has_cmake = False
    has_docker = False
    has_libraries = False
    
    try:
        subprocess.run(["cmake", "--version"], capture_output=True, check=True, timeout=5)
        has_cmake = True
    except:
        pass
    
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=5)
        has_docker = True
    except:
        pass
    
    # Check for pre-built libraries
    ffiam_lib_paths = [
        Path(__file__).parent / "independent" / "ffiam" / "pyffiam" / "src" / "pyffiam" / "external" / "libffiam_lib.so",
        Path(__file__).parent / "independent" / "ffiam" / "pyffiam" / "src" / "pyffiam" / "external" / "libffiam_lib_cpu.so"
    ]
    has_libraries = any(path.exists() for path in ffiam_lib_paths)
    
    # Skip FFIAM tests if no build method is available
    if not (has_cmake or has_docker or has_libraries):
        skip_marker = pytest.mark.skip(reason="FFIAM tests require CMake, Docker, or pre-built libraries")
        for item in ffiam_tests:
            item.add_marker(skip_marker)
        
        print(f"\n{'='*70}")
        print("FFIAM TESTS SKIPPED")
        print(f"{'='*70}")
        print("Reason: No build method available")
        print("- CMake: {'found' if has_cmake else 'NOT found'}")
        print("- Docker: {'found' if has_docker else 'NOT found'}")
        print("- Pre-built libraries: {'found' if has_libraries else 'NOT found'}")
        print("\nTo run FFIAM tests:")
        print("1. Install CMake 3.20+ OR")
        print("2. Install Docker and run ./quickstart.sh OR")
        print("3. Use pre-built FFIAM libraries")
        print(f"{'='*70}\n")