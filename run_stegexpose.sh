#!/bin/bash
# run_stegexpose.sh
# Runs StegExpose on the images dataset and appends results
# to the detection report.

STEGEXPOSE_JAR="tools/StegExpose/StegExpose.jar"
IMAGE_DIR="datasets/images"
REPORT_FILE="reports/detection_report.txt"
THRESHOLD="0.2"   # Default StegExpose threshold (0.0-1.0)

echo "=========================================="
echo " StegExpose Analysis"
echo "=========================================="

# Check Java
if ! command -v java &> /dev/null; then
    echo "[-] Java is not installed. Install openjdk-17-jdk and retry."
    exit 1
fi

# Check StegExpose jar
if [ ! -f "$STEGEXPOSE_JAR" ]; then
    echo "[-] StegExpose JAR not found at $STEGEXPOSE_JAR"
    echo "    Cloning StegExpose..."
    mkdir -p tools
    git clone https://github.com/b3dk7/StegExpose.git tools/StegExpose
    if [ ! -f "$STEGEXPOSE_JAR" ]; then
        echo "[-] StegExpose.jar still not found after cloning. Exiting."
        exit 1
    fi
fi

echo "[+] Running StegExpose on $IMAGE_DIR (threshold: $THRESHOLD)..."

# StegExpose outputs a CSV: filename, score, result (stego/clean)
SE_OUTPUT=$(java -jar "$STEGEXPOSE_JAR" "$IMAGE_DIR" "$THRESHOLD" 2>&1)

echo ""
echo "$SE_OUTPUT"
echo ""

# Append to detection report
{
echo ""
echo "=============================="
echo "STEGEXPOSE RESULTS"
echo "Threshold: $THRESHOLD"
echo "=============================="
echo "$SE_OUTPUT"
echo ""
} >> "$REPORT_FILE"

echo "[OK] StegExpose results appended to $REPORT_FILE"
