#!/bin/bash
# Upload demo video to YouTube and IPFS
# Usage: ./scripts/upload_demo_video.sh
#
# This script provides instructions and helper functions for uploading
# the demo video to both YouTube and IPFS for resilience and archival.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"

echo "=========================================="
echo "Demo Video Upload Helper"
echo "=========================================="
echo ""

# ============================================================
# Part 1: YouTube Upload Instructions
# ============================================================
echo "📹 YOUTUBE UPLOAD"
echo "=========================================="
echo ""
echo "Option A: Using yt-dlp (local video → YT upload not supported)"
echo "  - yt-dlp is designed for downloading, not uploading"
echo ""
echo "Option B: Direct YouTube Upload (Recommended)"
echo "  1. Visit: https://www.youtube.com/upload"
echo "  2. Select: meritscore-demo-v1.mp4"
echo "  3. Set title: 'MeritScore Demo - EthGlobal OpenAgents Hackathon'"
echo "  4. Set description:"
echo "     'Proof-of-Merit demonstration: Agent credit scoring with ZK proofs'"
echo "  5. Set visibility: Unlisted or Public"
echo "  6. Copy URL after upload completes"
echo ""
echo "Option C: Using Google Drive + Share Link"
echo "  1. Upload to Google Drive"
echo "  2. Get shareable link"
echo "  3. Extract video ID from link"
echo ""

# ============================================================
# Part 2: IPFS Upload Instructions
# ============================================================
echo ""
echo "📦 IPFS UPLOAD"
echo "=========================================="
echo ""
echo "Option A: Using web3.storage (Recommended)"
echo "  1. Visit: https://web3.storage"
echo "  2. Sign in with GitHub"
echo "  3. Upload meritscore-demo-v1.mp4"
echo "  4. Copy the IPFS CID (hash)"
echo "  5. Verify at: https://ipfs.io/ipfs/<CID>"
echo ""
echo "Option B: Using local IPFS node"
echo "  Requirements: IPFS daemon running (ipfs daemon)"
echo ""
IPFS_AVAILABLE=$(command -v ipfs &>/dev/null && echo "yes" || echo "no")
if [ "$IPFS_AVAILABLE" = "yes" ]; then
    echo "  ✓ IPFS command found on system"
    echo ""
    echo "  To upload:"
    echo "    ipfs add meritscore-demo-v1.mp4"
    echo ""
    echo "  Output will show:"
    echo "    added QmXxxx... meritscore-demo-v1.mp4"
    echo ""
else
    echo "  ⚠ IPFS command not found - install via: brew install ipfs"
    echo ""
fi

echo "Option C: Using pinata.cloud"
echo "  1. Visit: https://www.pinata.cloud"
echo "  2. Sign up / Log in"
echo "  3. Upload meritscore-demo-v1.mp4"
echo "  4. Copy IPFS hash"
echo ""

# ============================================================
# Part 3: Record URLs in docs/video-urls.md
# ============================================================
echo ""
echo "📝 STORING URLS"
echo "=========================================="
echo ""

VIDEO_URLS_FILE="$DOCS_DIR/video-urls.md"

cat > "$VIDEO_URLS_FILE" << 'EOF'
# Demo Video URLs

**Status**: Configure URLs below before demo day

## YouTube
- **URL**: [Add YouTube link here]
- **Title**: MeritScore Demo - EthGlobal OpenAgents Hackathon
- **Visibility**: Unlisted/Public
- **Length**: ~3-5 minutes

## IPFS
- **CID**: (Add IPFS hash here)
- **Gateway URLs**:
  - https://ipfs.io/ipfs/{CID}
  - https://gateway.pinata.cloud/ipfs/{CID}
  - https://dweb.link/ipfs/{CID}

## Backup
- **USB Drive 1**: ~/backup/meritscore-demo-v1.mp4
- **USB Drive 2**: ~/backup/meritscore-demo-v1.mp4

## Verification Checklist
- [ ] YouTube video plays and loads correctly
- [ ] IPFS CID resolves at gateway
- [ ] Video bitrate suitable for mobile networks
- [ ] Audio is clear and synced with video
- [ ] Demo flow matches DEMO_SCRIPT.md
EOF

echo "✓ Created: $VIDEO_URLS_FILE"
echo ""
echo "Edit the file to record URLs:"
echo "  nano $VIDEO_URLS_FILE"
echo ""

# ============================================================
# Part 4: Recommend ffmpeg for video preparation
# ============================================================
echo ""
echo "🎬 VIDEO PREPARATION (OPTIONAL)"
echo "=========================================="
echo ""
echo "Before uploading, consider optimizing with ffmpeg:"
echo ""
echo "1. Check current specs:"
echo "   ffprobe meritscore-demo-v1.mp4"
echo ""
echo "2. Optimize for mobile (reduce bitrate, keep quality):"
echo "   ffmpeg -i meritscore-demo-v1.mp4 -c:v libx264 -preset slow \\"
echo "     -crf 22 -c:a aac -b:a 128k output.mp4"
echo ""
echo "3. Compress for IPFS upload:"
echo "   ffmpeg -i meritscore-demo-v1.mp4 -c:v libx264 -preset fast \\"
echo "     -crf 28 -c:a aac -b:a 96k compressed.mp4"
echo ""
ffmpeg_available=$(command -v ffmpeg &>/dev/null && echo "yes" || echo "no")
if [ "$ffmpeg_available" = "yes" ]; then
    echo "✓ ffmpeg found on system"
else
    echo "⚠ ffmpeg not found - install via: brew install ffmpeg"
fi
echo ""

# ============================================================
# Part 5: Automated IPFS upload (if node available)
# ============================================================
echo ""
echo "⚡ QUICK UPLOAD (if IPFS node running)"
echo "=========================================="
echo ""
echo "To upload directly to local IPFS node:"
echo ""
echo "  ./scripts/upload_demo_video.sh --ipfs-add meritscore-demo-v1.mp4"
echo ""

if [ "$#" -gt 0 ] && [ "$1" = "--ipfs-add" ] && [ -n "$2" ]; then
    VIDEO_FILE="$2"

    if [ ! -f "$VIDEO_FILE" ]; then
        echo "❌ Error: Video file not found: $VIDEO_FILE"
        exit 1
    fi

    if [ "$IPFS_AVAILABLE" != "yes" ]; then
        echo "❌ Error: IPFS not installed or daemon not running"
        exit 1
    fi

    echo "Uploading to IPFS: $VIDEO_FILE"
    IPFS_OUTPUT=$(ipfs add "$VIDEO_FILE" 2>&1)

    # Extract the hash
    IPFS_HASH=$(echo "$IPFS_OUTPUT" | grep "added" | awk '{print $2}')

    if [ -n "$IPFS_HASH" ]; then
        echo ""
        echo "✅ Upload successful!"
        echo ""
        echo "IPFS Hash (CID): $IPFS_HASH"
        echo ""
        echo "View at:"
        echo "  - https://ipfs.io/ipfs/$IPFS_HASH"
        echo "  - https://gateway.pinata.cloud/ipfs/$IPFS_HASH"
        echo "  - https://dweb.link/ipfs/$IPFS_HASH"
        echo ""
        echo "Update video-urls.md with:"
        echo "  nano $VIDEO_URLS_FILE"
        echo ""
    else
        echo "❌ Failed to extract IPFS hash"
        echo "Output: $IPFS_OUTPUT"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Next steps:"
echo "  1. Prepare video (ffmpeg optional)"
echo "  2. Upload to YouTube"
echo "  3. Upload to IPFS (web3.storage or local node)"
echo "  4. Update docs/video-urls.md with both URLs"
echo "  5. Verify both URLs work before demo day"
echo "=========================================="
echo ""
