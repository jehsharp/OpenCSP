# Copyright 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

"""Pytest plugin for automatic FFIAM CMake build.

This plugin automatically builds the FFIAM C++ library using CMake before running tests,
ensuring that users can simply run `pytest` without manually building the library first.

To use this plugin, simply install pyffiam in development mode:
    pip install -e .

The plugin will be automatically discovered by pytest and will build the FFIAM library
before running any tests.
"""

import os
import subprocess
import sys
from pathlib import Path


def pytest_configure(config):
    """Build FFIAM library before running tests."""
    # Only build if we're actually running tests (not just collecting)
    if not hasattr(config, '_preconfig') or not config.option.collectonly:
        build_ffiam_library()


def build_ffiam_library():
    """Build the FFIAM C++ library using CMake or Docker."""
    # Find the ffiam directory
    ffiam_dir = find_ffiam_directory()
    if not ffiam_dir:
        print("FFIAM directory not found, skipping build")
        return
    
    # Check if libraries already exist
    cpu_lib_path = ffiam_dir.parent / "pyffiam" / "src" / "pyffiam" / "external" / "libffiam_lib_cpu.so"
    gpu_lib_path = ffiam_dir.parent / "pyffiam" / "src" / "pyffiam" / "external" / "libffiam_lib.so"
    
    if cpu_lib_path.exists() or gpu_lib_path.exists():
        print(f"FFIAM library already exists, skipping build")
        return
    
    # Try CMake first
    if try_cmake_build(ffiam_dir):
        return
    
    # Try Docker if CMake fails
    if try_docker_build(ffiam_dir):
        return
    
    # If neither works, provide clear guidance (but don't exit)
    print("\n" + "="*70)
    print("FFIAM BUILD SKIPPED - Missing dependencies")
    print("="*70)
    print("To run FFIAM tests, you need either:")
    print("1. CMake 3.20+ (for native build)")
    print("2. Docker (for containerized build)")
    print("\nFFIAM tests will be skipped during this test run.")
    print("="*70 + "\n")


def try_cmake_build(ffiam_dir: Path) -> bool:
    """Attempt to build FFIAM using CMake. Returns True if successful."""
    try:
        subprocess.run(["cmake", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("CMake not found - cannot build FFIAM natively")
        return False
    
    print(f"Building FFIAM library using CMake from: {ffiam_dir}")
    
    # Create build directory
    build_dir = ffiam_dir / "build"
    build_dir.mkdir(exist_ok=True)
    
    # Configure CMake
    cmake_cmd = [
        "cmake",
        "-B", str(build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CUDA_ARCHITECTURES=75;80;86;89;90;100;120"
    ]
    
    # Check if CUDA is available
    try:
        subprocess.run(["nvcc", "--version"], capture_output=True, check=True)
        print("CUDA detected - building with GPU support")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("CUDA not found - building CPU-only version")
        cmake_cmd.append("-DCMAKE_CUDA_COMPILER=OFF")
    
    print(f"Running: {' '.join(cmake_cmd)}")
    result = subprocess.run(cmake_cmd, cwd=ffiam_dir)
    if result.returncode != 0:
        print("CMake configuration failed")
        return False
    
    # Build the appropriate library target(s)
    build_targets = ["ffiam_lib_cpu"]  # Always build CPU version
    
    # Only add GPU target if CUDA is available
    if "-DCMAKE_CUDA_COMPILER=OFF" not in cmake_cmd:
        build_targets.append("ffiam_lib")
    
    build_cmd = ["cmake", "--build", str(build_dir), "--target"] + build_targets
    print(f"Running: {' '.join(build_cmd)}")
    result = subprocess.run(build_cmd, cwd=ffiam_dir)
    if result.returncode != 0:
        print("CMake build failed")
        return False
    
    print("FFIAM library build completed successfully using CMake")
    return True


def try_docker_build(ffiam_dir: Path) -> bool:
    """Attempt to build FFIAM using Docker. Returns True if successful."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Docker not found - cannot build FFIAM in container")
        return False
    
    print("Building FFIAM library using Docker...")
    
    # Check if image exists, build if not
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", "ffiam"],
            capture_output=True,
            timeout=30
        )
        if result.returncode != 0:
            print("FFIAM Docker image not found - building it...")
            build_result = subprocess.run(
                ["docker", "build", "-t", "ffiam", "."],
                cwd=ffiam_dir.parent,
                capture_output=True,
                text=True,
                timeout=600
            )
            if build_result.returncode != 0:
                print(f"Docker build failed: {build_result.stderr}")
                return False
    except subprocess.TimeoutExpired:
        print("Docker operation timed out")
        return False
    
    # Copy libraries from container to host
    print("Extracting built libraries from Docker container...")
    try:
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{ffiam_dir.parent}/pyffiam/src/pyffiam/external:/output",
            "ffiam",
            "bash", "-c",
            "cp /opt/ffiam/pyffiam/src/pyffiam/external/libffiam_lib* /output/"
        ], check=True, capture_output=True)
        print("FFIAM library build completed successfully using Docker")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract libraries from Docker container: {e}")
        return False


def find_ffiam_directory() -> Path:
    """Find the ffiam directory relative to the current file."""
    current_file = Path(__file__)
    
    # Look for ffiam directory in common locations
    possible_locations = [
        current_file.parent.parent.parent / "ffiam",  # pyffiam/tests/ -> pyffiam/ -> ffiam/
        current_file.parent.parent.parent.parent / "independent" / "ffiam" / "ffiam",  # projects/independent/ffiam/ffiam
    ]
    
    for location in possible_locations:
        if location.exists() and (location / "CMakeLists.txt").exists():
            return location
    
    return None


def pytest_sessionstart(session):
    """Ensure the library is built at the start of the test session."""
    build_ffiam_library()