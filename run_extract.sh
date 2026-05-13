#!/bin/bash

echo "========================================="
echo " Hidden Payload Extraction"
echo "========================================="

source venv/bin/activate

echo ""
echo "[1/3] Extracting from stego images (steghide)..."
python3 scripts/extract_data.py

echo ""
echo "[2/3] Extracting from audio and video files..."
python3 scripts/extract_audio_video.py

echo ""
echo "[3/3] Regenerating consolidated report with extraction results..."
python3 scripts/generate_report.py

echo ""
echo "========================================="
echo " Extraction complete."
echo " Image payloads  -> extracted/images/"
echo " Audio payloads  -> extracted/audio/"
echo " Video payloads  -> extracted/videos/"
echo " Full report     -> reports/final_report.txt"
echo " Extraction log  -> reports/extraction_report.txt"
echo "========================================="
