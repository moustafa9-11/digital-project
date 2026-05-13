#!/bin/bash

echo "========================================="
echo " Installing Steganography Forensics Lab"
echo " (Kali Linux Optimization)"
echo "========================================="

# Update package list
sudo apt update

# Python tools
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Steganography & Forensics tools (Kali specific)
echo "[*] Installing core forensics tools..."
sudo apt install -y steghide
sudo apt install -y stegseek      # Faster than stegcracker, standard on Kali
sudo apt install -y exiftool
sudo apt install -y foremost
sudo apt install -y binwalk
sudo apt install -y ffmpeg
sudo apt install -y audacity
sudo apt install -y git
sudo apt install -y openjdk-17-jdk
sudo apt install -y ruby-full      # Required for zsteg
sudo gem install zsteg             # Powerful PNG/BMP stego detection

# Check for stegcracker (it's often replaced by stegseek on newer Kali)
sudo apt install -y stegcracker 2>/dev/null || echo "[!] stegcracker not in repo, using stegseek as alternative"

# Unzip rockyou wordlist if on Kali
if [ -f /usr/share/wordlists/rockyou.txt.gz ] && [ ! -f /usr/share/wordlists/rockyou.txt ]; then
    echo "[*] Unzipping rockyou wordlist..."
    sudo gunzip /usr/share/wordlists/rockyou.txt.gz
fi

# Python virtual environment
echo "[*] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Ensure scripts are executable
chmod +x run_scan.sh
chmod +x run_extract.sh
chmod +x run_stegexpose.sh
chmod +x clear_reports.sh

echo "========================================="
echo " Installation Complete"
echo " Environment ready for Kali Linux"
echo "========================================="
