#!/bin/bash
# Build script for SOFAST binary using PyInstaller

echo "Building SOFAST binary..."
echo "=========================="
echo ""

# Display build environment info
echo "Build Environment:"
echo "  Host: $(hostname)"
echo "  Date: $(date)"
echo "  Python: $(python3 --version 2>&1)"
echo "  GLIBC: $(ldd --version 2>&1 | head -1)"
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null && ! python3 -m PyInstaller --version &> /dev/null; then
    echo "Error: PyInstaller is not installed"
    echo "Install it with: pip install pyinstaller"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Build using the spec file
echo "Running PyInstaller..."
if command -v pyinstaller &> /dev/null; then
    pyinstaller sofast.spec
else
    python3 -m PyInstaller sofast.spec
fi

# Check if build was successful
if [ $? -eq 0 ]; then
    # Create build info file
    echo "Creating build information file..."
    cat > dist/sofast/BUILD_INFO.txt << EOF
SOFAST Binary Build Information
================================

Build Date: $(date)
Build Host: $(hostname)
Python Version: $(python3 --version 2>&1)
GLIBC Version: $(ldd --version 2>&1 | head -1)
PyInstaller Version: $(python3 -m PyInstaller --version 2>&1)

Minimum GLIBC Required:
$(objdump -T dist/sofast/sofast 2>/dev/null | grep GLIBC | sed 's/.*GLIBC_/GLIBC_/' | sort -V | tail -1 || echo "Unable to determine")

Binary will run on:
- Systems with the same or newer GLIBC version
- Same architecture ($(uname -m))

For compatibility issues, see: GLIBC_COMPATIBILITY_GUIDE.md
EOF

    echo ""
    echo "=========================="
    echo "Build completed successfully!"
    echo ""
    echo "Binary location: dist/sofast/sofast"
    echo "Build info: dist/sofast/BUILD_INFO.txt"
    echo ""
    echo "Build Environment Summary:"
    echo "  GLIBC: $(ldd --version 2>&1 | head -1 | grep -oP '\d+\.\d+' | head -1)"
    echo "  Arch: $(uname -m)"
    echo ""
    echo "⚠️  Note: This binary requires GLIBC $(ldd --version 2>&1 | head -1 | grep -oP '\d+\.\d+' | head -1)+"
    echo "   Build on older systems for wider compatibility"
    echo ""
    echo "To run the binary:"
    echo "  cd dist/sofast"
    echo "  ./sofast"
    echo "=========================="
else
    echo ""
    echo "Build failed! Please check the errors above."
    exit 1
fi
