# Digital Steganography Forensics Lab

A comprehensive toolkit for detecting and extracting hidden data from images, audio, and video files.

## Supported OS
- **Ubuntu** (Standard support)
- **Kali Linux** (Optimized support with additional tools)

## Installation
```bash
chmod +x setup.sh
./setup.sh
```

## Run Detection
```bash
./run_scan.sh
```

## Run Extraction
```bash
./run_extract.sh
```

## Open Dashboard
```bash
cd dashboard
python3 serve.py
```

## Kali Linux Specifics
The `setup.sh` script on Kali will automatically:
- Install `stegseek` (faster alternative to stegcracker).
- Install `zsteg` for advanced PNG/BMP analysis.
- Unzip the `rockyou.txt` wordlist if it's currently compressed.