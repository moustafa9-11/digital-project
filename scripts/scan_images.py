import os
import subprocess
from colorama import Fore, init

init(autoreset=True)

STEGO_DIR = "datasets/images"
REPORT_FILE = "reports/detection_report.txt"


def run_steghide_check(image_path):
    result = subprocess.run(
        ["steghide", "info", image_path, "-p", ""],
        capture_output=True,
        text=True
    )

    if "could not extract" in result.stderr or "could not extract" in result.stdout:
        return "No steghide payload detected (or wrong passphrase)"
    
    return result.stdout


def run_exiftool(image_path):
    try:
        result = subprocess.run(
            ["exiftool", image_path],
            capture_output=True,
            text=True
        )

        return result.stdout

    except Exception as e:
        return str(e)


with open(REPORT_FILE, "w") as report:

    report.write("STEGANOGRAPHY DETECTION REPORT\n")
    report.write("=" * 60 + "\n\n")

    for file in os.listdir(STEGO_DIR):

        image_path = os.path.join(STEGO_DIR, file)

        print(Fore.CYAN + f"Scanning: {file}")

        report.write(f"FILE: {file}\n")
        report.write("-" * 50 + "\n")

        steghide_output = run_steghide_check(image_path)
        exif_output = run_exiftool(image_path)

        report.write("[STEGO INFO]\n")
        report.write(steghide_output + "\n")

        report.write("[EXIF ANALYSIS]\n")
        report.write(exif_output + "\n")

        report.write("\n\n")

print(Fore.GREEN + "Detection scan complete.")
