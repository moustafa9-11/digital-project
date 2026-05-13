#!/bin/bash
# clear_reports.sh
# Clears all report files before running new analysis

echo "Clearing all report files..."

# Clear detection report (this gets rebuilt by scan scripts)
> reports/detection_report.txt

# Clear extraction report (this gets rebuilt by extract scripts)  
> reports/extraction_report.txt

# Clear entropy report (this gets rebuilt by entropy analysis)
> reports/entropy_report.txt

# Clear final report (this gets rebuilt by generate_report.py)
> reports/final_report.txt

echo "All report files cleared."
