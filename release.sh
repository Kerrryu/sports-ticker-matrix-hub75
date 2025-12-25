#!/bin/bash
# Sports Ticker Release Script
# Usage: ./release.sh 1.0.1 "Fixed display bug, added new feature"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: ./release.sh <version> [changelog]"
    echo "Example: ./release.sh 1.0.1 \"Fixed display bug\""
    exit 1
fi

VERSION=$1
CHANGELOG=${2:-"Version $VERSION release"}

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}Sports Ticker Release Script${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""
echo -e "Version: ${GREEN}$VERSION${NC}"
echo -e "Changelog: ${GREEN}$CHANGELOG${NC}"
echo ""

# Confirm
read -p "Proceed with release? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Update version.json
echo -e "${YELLOW}Updating version.json...${NC}"
cat > version.json << EOF
{
  "version": "$VERSION",
  "installed": 0,
  "build": "prod",
  "name": "Sports Ticker",
  "changelog": "$CHANGELOG",
  "download_url": "https://github.com/Kerrryu/sports-ticker-matrix-hub75/archive/refs/tags/v$VERSION.tar.gz",
  "checksum": ""
}
EOF

# Update main.py version
echo -e "${YELLOW}Updating main.py version...${NC}"
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" main.py

# Git add and commit
echo -e "${YELLOW}Committing changes...${NC}"
git add -A
git commit -m "Release v$VERSION - $CHANGELOG"

# Create and push tag
echo -e "${YELLOW}Creating tag v$VERSION...${NC}"
git tag -a "v$VERSION" -m "$CHANGELOG"

# Push everything
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push origin main
git push origin "v$VERSION"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Release v$VERSION complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com/Kerrryu/sports-ticker-matrix-hub75/releases"
echo "2. Click on the v$VERSION tag"
echo "3. Click 'Create release from tag' (optional, for release notes)"
echo ""
echo "The device will detect the update when it checks version.json"
