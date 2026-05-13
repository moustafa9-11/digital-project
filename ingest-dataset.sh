#!/bin/bash

echo "========================================="
echo " Ingesting Clean and Stego Dataset"
echo "========================================="

BASE_DIR="$(pwd)"

# Directories
CLEAN_IMG="$BASE_DIR/datasets/images"
CLEAN_AUDIO="$BASE_DIR/datasets/audio"
CLEAN_VIDEO="$BASE_DIR/datasets/clean/videos"

STEGO_IMG="$BASE_DIR/datasets/images"
STEGO_AUDIO="$BASE_DIR/datasets/audio"
STEGO_VIDEO="$BASE_DIR/datasets/videos"

TMP_DIR="$BASE_DIR/tmp_dataset"

mkdir -p "$TMP_DIR"

# -----------------------------------------
# VERIFY REQUIRED TOOLS
# -----------------------------------------

required_tools=(
    steghide
    ffmpeg
    exiftool
    binwalk
    foremost
)

echo "[+] Checking required tools..."

for tool in "${required_tools[@]}"
do
    if ! command -v $tool &> /dev/null
    then
        echo "[-] $tool is NOT installed."
        exit 1
    else
        echo "[OK] $tool"
    fi
done

# -----------------------------------------
# CLEAN IMAGE DATASET
# -----------------------------------------

echo ""
echo "[+] Downloading clean images..."

wget -q -O "$CLEAN_IMG/clean_1.jpg" https://picsum.photos/800/600
wget -q -O "$CLEAN_IMG/clean_2.jpg" https://picsum.photos/1024/768
wget -q -O "$CLEAN_IMG/clean_3.jpg" https://picsum.photos/1200/900

echo "[OK] Clean image dataset ready."

# -----------------------------------------
# SECRET PAYLOADS
# -----------------------------------------

echo ""
echo "[+] Creating hidden payload files..."

cat <<EOF > "$TMP_DIR/secret_1.txt"
Case ID: DF-2026-001
Evidence Type: Hidden Communication
Classification: Confidential
EOF

cat <<EOF > "$TMP_DIR/secret_2.txt"
Malware IOC:
185.244.25.21
Suspicious Beacon Detected
EOF

cat <<EOF > "$TMP_DIR/secret_3.txt"
Digital Forensics Lab
Hidden Payload Demonstration
EOF

echo "[OK] Payload files created."

# -----------------------------------------
# GENERATE STEGO IMAGES
# USING STEGHIDE (PROJECT TOOL)
# -----------------------------------------

echo ""
echo "[+] Generating stego images..."

cp "$CLEAN_IMG/clean_1.jpg" "$STEGO_IMG/stego_1.jpg"
cp "$CLEAN_IMG/clean_2.jpg" "$STEGO_IMG/stego_2.jpg"
cp "$CLEAN_IMG/clean_3.jpg" "$STEGO_IMG/stego_3.jpg"

steghide embed \
-cf "$STEGO_IMG/stego_1.jpg" \
-ef "$TMP_DIR/secret_1.txt" \
-p 1234 \
-f > /dev/null 2>&1

steghide embed \
-cf "$STEGO_IMG/stego_2.jpg" \
-ef "$TMP_DIR/secret_2.txt" \
-p 1234 \
-f > /dev/null 2>&1

steghide embed \
-cf "$STEGO_IMG/stego_3.jpg" \
-ef "$TMP_DIR/secret_3.txt" \
-p 1234 \
-f > /dev/null 2>&1

echo "[OK] Stego image dataset created."

# -----------------------------------------
# AUDIO DATASET
# USING FFMPEG + AUDACITY WORKFLOW
# -----------------------------------------

echo ""
echo "[+] Creating audio dataset..."

ffmpeg -f lavfi \
-i anullsrc=r=44100:cl=mono \
-t 5 \
-q:a 9 \
-acodec libmp3lame \
"$CLEAN_AUDIO/clean_audio.mp3" \
-y > /dev/null 2>&1

cp "$CLEAN_AUDIO/clean_audio.mp3" \
"$STEGO_AUDIO/stego_audio.mp3"

echo "Hidden audio payload" > "$TMP_DIR/audio_secret.txt"

cat "$TMP_DIR/audio_secret.txt" >> \
"$STEGO_AUDIO/stego_audio.mp3"

echo "[OK] Audio dataset created."

# -----------------------------------------
# VIDEO DATASET
# USING FFMPEG
# -----------------------------------------

echo ""
echo "[+] Creating video dataset..."

ffmpeg \
-f lavfi \
-i testsrc=size=1280x720:rate=30 \
-t 5 \
"$CLEAN_VIDEO/clean_video.mp4" \
-y > /dev/null 2>&1

cp "$CLEAN_VIDEO/clean_video.mp4" \
"$STEGO_VIDEO/stego_video.mp4"

echo "Hidden video payload" > "$TMP_DIR/video_secret.txt"

cat "$TMP_DIR/video_secret.txt" >> \
"$STEGO_VIDEO/stego_video.mp4"

echo "[OK] Video dataset created."

# -----------------------------------------
# OPTIONAL FORENSIC VALIDATION
# USING PROJECT TOOLS
# -----------------------------------------

echo ""
echo "[+] Running forensic validation..."

echo ""
echo "========== EXIFTOOL =========="
exiftool "$STEGO_IMG/stego_1.jpg" | head

echo ""
echo "========== BINWALK =========="
binwalk "$STEGO_IMG/stego_1.jpg"

echo ""
echo "========== STRINGS =========="
strings "$STEGO_IMG/stego_1.jpg" | head

# -----------------------------------------
# FINAL SUMMARY
# -----------------------------------------

echo ""
echo "========================================="
echo " Dataset Ingestion Completed"
echo "========================================="

echo ""
echo "[Clean Images]"
ls -lh "$CLEAN_IMG"

echo ""
echo "[Stego Images]"
ls -lh "$STEGO_IMG"

echo ""
echo "[Clean Audio]"
ls -lh "$CLEAN_AUDIO"

echo ""
echo "[Stego Audio]"
ls -lh "$STEGO_AUDIO"

echo ""
echo "[Clean Videos]"
ls -lh "$CLEAN_VIDEO"

echo ""
echo "[Stego Videos]"
ls -lh "$STEGO_VIDEO"

echo ""
echo "Steghide Password:"
echo "1234"

echo ""
echo "Next Steps:"
echo "./run_scan.sh"
echo "./run_extract.sh"
