#!/bin/bash

echo "========================================="
echo " Installing Steganography Forensics Lab"
echo "========================================="

sudo apt update

# Python tools
sudo apt install -y python3 python3-pip python3-venv

# Steganography tools
sudo apt install -y steghide
sudo apt install -y stegcracker
sudo apt install -y exiftool
sudo apt install -y foremost
sudo apt install -y binwalk
sudo apt install -y ffmpeg
sudo apt install -y audacity
sudo apt install -y git
sudo apt install -y openjdk-17-jdk


# Python virtual environment
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt


chmod +x run_scan.sh
chmod +x run_extract.sh
chmod +x run_stegexpose.sh


echo "========================================="
echo " Installation Complete"
echo "========================================="
