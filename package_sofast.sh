#!/bin/bash
# Package the SOFAST binary for distribution

echo "Packaging SOFAST binary..."
echo "=========================="
echo ""

# Check if dist/sofast exists
if [ ! -d "dist/sofast" ]; then
    echo "Error: dist/sofast directory not found"
    echo "Please build the binary first with: ./build_sofast.sh"
    exit 1
fi

# Get version info if available
VERSION="1.0.0"
DATE=$(date +%Y%m%d)
PLATFORM="linux-x64"

# Create package name
PACKAGE_NAME="sofast-${VERSION}-${PLATFORM}-${DATE}.tar.gz"

echo "Creating package: ${PACKAGE_NAME}"
echo ""

# Create archive
cd dist
tar -czf "../${PACKAGE_NAME}" sofast/
cd ..

# Check if successful
if [ $? -eq 0 ]; then
    SIZE=$(du -h "${PACKAGE_NAME}" | cut -f1)
    echo ""
    echo "=========================="
    echo "Package created successfully!"
    echo ""
    echo "Package: ${PACKAGE_NAME}"
    echo "Size: ${SIZE}"
    echo ""
    echo "To distribute:"
    echo "  1. Send ${PACKAGE_NAME} to users"
    echo "  2. Users extract: tar -xzf ${PACKAGE_NAME}"
    echo "  3. Users run: cd sofast && ./sofast"
    echo "=========================="
else
    echo ""
    echo "Error: Failed to create package"
    exit 1
fi
