#!/bin/bash
# Copyright 2026 Scion Frontiers & Antigravity
# Build & Bundle script for Harness-Suprem.app on macOS Desktop

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Harness-Suprem"
DESKTOP_DIR="/Users/rarescristea/Desktop"
STAGE_APP="/tmp/${APP_NAME}.app"
TARGET_APP="${DESKTOP_DIR}/${APP_NAME}.app"

echo "[build] Compiling Native macOS SwiftUI App (${APP_NAME})..."

# 1. Compile Swift sources using native Apple Swift compiler
SOURCES=(
    "${SCRIPT_DIR}/Sources/Models.swift"
    "${SCRIPT_DIR}/Sources/MemPalaceService.swift"
    "${SCRIPT_DIR}/Sources/MLXClient.swift"
    "${SCRIPT_DIR}/Sources/ContentView.swift"
    "${SCRIPT_DIR}/Sources/main.swift"
)

BUILD_BIN="/tmp/${APP_NAME}_bin"
swiftc -O -target arm64-apple-macos14.0 \
    "${SOURCES[@]}" \
    -o "$BUILD_BIN"

echo "[build] Compilation successful."

# 2. Assemble .app bundle in neutral local staging directory
echo "[build] Creating application bundle structure..."
rm -rf "$STAGE_APP"
mkdir -p "${STAGE_APP}/Contents/MacOS"
mkdir -p "${STAGE_APP}/Contents/Resources/engine"

# Copy compiled binary
cp "$BUILD_BIN" "${STAGE_APP}/Contents/MacOS/${APP_NAME}"
chmod +x "${STAGE_APP}/Contents/MacOS/${APP_NAME}"

# Copy MLX bridge engine
cp "${SCRIPT_DIR}/engine/mlx_bridge.py" "${STAGE_APP}/Contents/Resources/engine/mlx_bridge.py"
chmod +x "${STAGE_APP}/Contents/Resources/engine/mlx_bridge.py"

# Create launcher wrapper that ensures MLX is ready
cat << 'EOF' > "${STAGE_APP}/Contents/MacOS/launch_engine.sh"
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES_DIR="${DIR}/../Resources"

# Start MLX engine in background if not already running
python3 "${RESOURCES_DIR}/engine/mlx_bridge.py" --start --port 5248 >/dev/null 2>&1 &

# Exec UI
exec "${DIR}/Harness-Suprem" "$@"
EOF
chmod +x "${STAGE_APP}/Contents/MacOS/launch_engine.sh"

# 3. Write Info.plist
cat << EOF > "${STAGE_APP}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch_engine.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.scion.harness-suprem</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
</dict>
</plist>
EOF

# 4. Clean extended attributes & Perform ad-hoc codesign in staging
xattr -cr "$STAGE_APP" || true

if command -v codesign >/dev/null 2>&1; then
    echo "[build] Applying ad-hoc codesign signature..."
    codesign -s - --force --deep "$STAGE_APP"
    codesign -v "$STAGE_APP"
fi

# 5. Deploy cleanly to Desktop
echo "[build] Deploying to Desktop: ${TARGET_APP}"
rm -rf "$TARGET_APP"
cp -R "$STAGE_APP" "$TARGET_APP"

echo "==========================================================="
echo "  Harness-Suprem.app built & installed successfully!"
echo "  Location: ${TARGET_APP}"
echo "  To launch: open ${TARGET_APP}"
echo "==========================================================="
