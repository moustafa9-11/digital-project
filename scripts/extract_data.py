import os
import subprocess
from colorama import Fore, init

init(autoreset=True)

STEGO_DIR = "datasets/images"
OUTPUT_DIR = "extracted/images"
PASSWORD = "1234"
REPORT_FILE = "reports/extraction_report.txt"

def write_extraction_report(filename, status, message, payload_preview=None, output_path=None):
    """Write extraction results to report file"""
    with open(REPORT_FILE, "a") as report:
        report.write(f"FILE: {filename}\n")
        report.write("-" * 50 + "\n")
        report.write(f"Status  : {status}\n")
        report.write(f"Details : {message}\n")
        if output_path and os.path.exists(output_path):
            report.write(f"Output  : {output_path}\n")
            if payload_preview:
                report.write("Payload :\n")
                report.write(payload_preview + "\n")
        report.write("\n")

# Clear the report file and initialize for images
with open(REPORT_FILE, "w") as report:
    report.write("\n\n" + "=" * 60 + "\n")
    report.write("IMAGE EXTRACTION RESULTS (Steghide)\n")
    report.write("=" * 60 + "\n\n")

for file in os.listdir(STEGO_DIR):

    image_path = os.path.join(STEGO_DIR, file)

    output_file = os.path.join(
        OUTPUT_DIR,
        f"extracted_{os.path.splitext(file)[0]}.txt"
    )

    print(Fore.YELLOW + f"Extracting from {file}")

    try:

        command = [
            "steghide",
            "extract",
            "-sf",
            image_path,
            "-p",
            PASSWORD,
            "-xf",
            output_file,
            "-f"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        print(result.stdout)
        
        # Determine success and write to report
        if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Success - read payload for preview
            payload_preview = None
            try:
                with open(output_file, "r") as f:
                    payload_content = f.read().strip()
                    if payload_content:  # Check if there's actual content
                        payload_preview = payload_content[:200] + ("..." if len(payload_content) > 200 else "")
                        
                        write_extraction_report(
                            file, 
                            "SUCCESS", 
                            "Steghide extraction successful", 
                            payload_preview, 
                            output_file
                        )
                        print(Fore.GREEN + f"  [SUCCESS] Payload extracted from {file}")
                    else:
                        # File exists but empty - treat as failure
                        write_extraction_report(
                            file, 
                            "FAIL", 
                            "Steghide extraction failed: Empty payload file"
                        )
                        print(Fore.RED + f"  [FAIL] Empty payload from {file}")
            except Exception as e:
                write_extraction_report(
                    file, 
                    "FAIL", 
                    f"Steghide extraction failed: Could not read payload - {e}"
                )
                print(Fore.RED + f"  [ERROR] Could not read payload from {file}")
        else:
            # Failure
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not error_msg:
                error_msg = "No payload found or wrong password"
            write_extraction_report(
                file, 
                "FAIL", 
                f"Steghide extraction failed: {error_msg}"
            )
            print(Fore.RED + f"  [FAIL] No payload found in {file}")

    except Exception as e:
        error_msg = str(e)
        write_extraction_report(
            file, 
            "FAIL", 
            f"Extraction error: {error_msg}"
        )
        print(Fore.RED + f"  [ERROR] {error_msg}")


print(Fore.GREEN + "Extraction process completed.")
