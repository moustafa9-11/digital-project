#!/bin/bash

echo "========================================="
echo " Steganography Detection Scan"
echo "========================================="

source venv/bin/activate

echo ""
echo "[1/5] Scanning images (steghide + exiftool)..."
python3 scripts/scan_images.py

echo ""
echo "[2/5] Entropy analysis..."
python3 scripts/entropy_analysis.py

echo ""
echo "[3/5] Scanning audio and video files..."
python3 scripts/scan_audio_video.py

echo ""
echo "[4/5] Embedding algorithm analysis (clean vs stego)..."
python3 scripts/analyze_algorithms.py

echo ""
echo "[5/5] Running StegExpose on images..."
./run_stegexpose.sh

echo ""
echo "[+] Generating consolidated report..."
python3 scripts/generate_report.py

echo ""
echo "========================================="
echo " Scan complete. Reports in reports/"
echo "========================================="
