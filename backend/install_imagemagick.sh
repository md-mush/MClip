#!/bin/bash

echo "🚀 Installing ImageMagick for Google Colab"
echo "=========================================="

# Update package lists
echo "📦 Updating package lists..."
apt-get update -y

# Install ImageMagick and dependencies
echo "🎨 Installing ImageMagick..."
apt-get install -y imagemagick imagemagick-dev

# Install additional dependencies for better font support
echo "🔤 Installing font libraries..."
apt-get install -y libfontconfig1-dev libfreetype6-dev

# Install common fonts
echo "📝 Installing common fonts..."
apt-get install -y fonts-dejavu-core fonts-liberation ttf-mscorefonts-installer

# Configure ImageMagick policy for MoviePy compatibility
echo "⚙️  Configuring ImageMagick policy..."
POLICY_FILE="/etc/ImageMagick-6/policy.xml"

if [ -f "$POLICY_FILE" ]; then
    # Backup original policy
    cp "$POLICY_FILE" "${POLICY_FILE}.backup"
    
    # Remove restrictive policies that interfere with MoviePy
    sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<policy domain="path" rights="read|write" pattern="@*"/g' "$POLICY_FILE"
    sed -i 's/<policy domain="coder" rights="none" pattern="PDF"/<policy domain="coder" rights="read|write" pattern="PDF"/g' "$POLICY_FILE"
    sed -i 's/<policy domain="coder" rights="none" pattern="LABEL"/<policy domain="coder" rights="read|write" pattern="LABEL"/g' "$POLICY_FILE"
    
    echo "✅ ImageMagick policy updated for MoviePy compatibility"
else
    echo "⚠️  ImageMagick policy file not found at $POLICY_FILE"
fi

# Test ImageMagick installation
echo "🧪 Testing ImageMagick installation..."
if command -v convert &> /dev/null; then
    echo "✅ ImageMagick 'convert' command is available"
    convert -version | head -n 1
else
    echo "❌ ImageMagick 'convert' command not found"
fi

if command -v magick &> /dev/null; then
    echo "✅ ImageMagick 'magick' command is available"
    magick -version | head -n 1
else
    echo "❌ ImageMagick 'magick' command not found"
fi

# Test font availability
echo "🔤 Testing font availability..."
fc-list | grep -i arial | head -n 3
fc-list | grep -i dejavu | head -n 3

echo "🎉 ImageMagick installation complete!"
echo "=========================================="