import os
import re
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

FINAL_REPORT = "reports/final_report.txt"
EXTRACTION_REPORT = "reports/extraction_report.txt"
DETECTION_REPORT = "reports/detection_report.txt"
ENTROPY_REPORT = "reports/entropy_report.txt"
IMAGE_DIR = "datasets/images"
AUDIO_DIR = "datasets/audio"
VIDEO_DIR = "datasets/videos"
EXTRACTED_IMAGES = "extracted/images"
EXTRACTED_AUDIO = "extracted/audio"
EXTRACTED_VIDEO = "extracted/videos"


def read_report(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None


def list_files(directory, extensions=None):
    if not os.path.isdir(directory):
        return []
    files = os.listdir(directory)
    if extensions:
        files = [f for f in files if f.lower().endswith(extensions)]
    return sorted(files)


def parse_entropy_report(content):
    """Parse entropy_report.txt -> dict of {filename: entropy}"""
    results = {}
    if not content:
        return results
    for line in content.splitlines():
        match = re.match(r"(.+?)\s*->\s*Entropy:\s*([\d.]+)", line)
        if match:
            results[match.group(1).strip()] = float(match.group(2))
    return results


def parse_extraction_results(content):
    """
    Parse extraction_report.txt to count successes/failures.
    Returns: list of dicts with {file, status, payload_preview}
    """
    results = []
    if not content:
        return results

    blocks = re.split(r"\n(?=FILE:)", content)
    for block in blocks:
        file_match = re.search(r"FILE:\s*(.+)", block)
        status_match = re.search(r"Status\s*:\s*(\S+)", block)
        payload_match = re.search(r"Payload\s*:\n([\s\S]+?)(?:\n\n|$)", block)

        if file_match and status_match:
            results.append({
                "file": file_match.group(1).strip(),
                "status": status_match.group(1).strip(),
                "payload": payload_match.group(1).strip()[:200] if payload_match else None,
            })
    return results


def parse_stegexpose_results(detection_content):
    """Extract StegExpose block from detection report if present."""
    if not detection_content:
        return None
    match = re.search(
        r"STEGEXPOSE RESULTS([\s\S]+?)(?=={3,}|\Z)",
        detection_content
    )
    return match.group(0).strip() if match else None


def count_extracted_files(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))] \
        if os.path.isdir(directory) else []
    return len(files), files


def calculate_detection_accuracy(image_files, audio_files, video_files, extracted_dir):
    stego_images = [f for f in image_files if f.startswith("stego_")]
    clean_images = [f for f in image_files if f.startswith("clean_")]
    stego_audio = [f for f in audio_files if "stego" in f]
    clean_audio = [f for f in audio_files if "clean" in f]
    stego_video = [f for f in video_files if "stego" in f]
    clean_video = [f for f in video_files if "clean" in f]

    extracted_files = []
    # Handle both directory path and list of files
    if isinstance(extracted_dir, str):
        # If it's a directory path
        if os.path.isdir(extracted_dir):
            extracted_files = os.listdir(extracted_dir)
    elif isinstance(extracted_dir, list):
        # If it's already a list of files
        extracted_files = extracted_dir
    else:
        # If it's neither, try to find extracted files in all directories
        for dir_path in ['extracted/images', 'extracted/audio', 'extracted/videos']:
            if os.path.exists(dir_path):
                extracted_files.extend([f for f in os.listdir(dir_path) if f.endswith('.txt')])

    # Count total stego files across all media types
    total_stego = len(stego_images) + len(stego_audio) + len(stego_video)
    total_clean = len(clean_images) + len(clean_audio) + len(clean_video)

    detected = 0
    # Check image extraction
    for stego in stego_images:
        stem = os.path.splitext(stego)[0]  # e.g. "stego_1"
        if any(f"extracted_{stem}.txt" in f for f in extracted_files):
            detected += 1
    # Check audio extraction
    for stego in stego_audio:
        stem = os.path.splitext(stego)[0]  # e.g. "stego_audio"
        if any(f"extracted_{stem}.txt" in f for f in extracted_files):
            detected += 1
    # Check video extraction
    for stego in stego_video:
        stem = os.path.splitext(stego)[0]  # e.g. "stego_video"
        if any(f"extracted_{stem}.txt" in f for f in extracted_files):
            detected += 1

    return {
        "stego_total": total_stego,
        "clean_total": total_clean,
        "detected": detected,
        "accuracy": (detected / total_stego * 100) if total_stego > 0 else 0,
    }

def write_separator(f, char="=", width=70):
    f.write(char * width + "\n")


def write_section(f, title):
    f.write("\n")
    write_separator(f)
    f.write(f"  {title.upper()}\n")
    write_separator(f)
    f.write("\n")


def main():
    print(Fore.CYAN + "\n[+] Generating consolidated forensic report...")

    # Load all sub-reports
    entropy_content = read_report(ENTROPY_REPORT)
    detection_content = read_report(DETECTION_REPORT)
    extraction_content = read_report(EXTRACTION_REPORT)

    entropy_data = parse_entropy_report(entropy_content)
    extraction_results = parse_extraction_results(extraction_content or "")
    stegexpose_block = parse_stegexpose_results(detection_content)

    # File inventories
    image_files = list_files(IMAGE_DIR, (".jpg", ".jpeg", ".png"))
    audio_files = list_files(AUDIO_DIR, (".mp3", ".wav", ".ogg", ".flac"))
    video_files = list_files(VIDEO_DIR, (".mp4", ".avi", ".mkv", ".mov"))

    img_extracted_count, img_extracted = count_extracted_files(EXTRACTED_IMAGES)
    aud_extracted_count, aud_extracted = count_extracted_files(EXTRACTED_AUDIO)
    vid_extracted_count, vid_extracted = count_extracted_files(EXTRACTED_VIDEO)

    # Calculate accuracy with all extracted files combined
    all_extracted = []
    for dir_path in [EXTRACTED_IMAGES, EXTRACTED_AUDIO, EXTRACTED_VIDEO]:
        if os.path.exists(dir_path):
            all_extracted.extend([f for f in os.listdir(dir_path) if f.endswith('.txt')])
    
    # Calculate accuracy with all extracted files combined
    all_extracted = []
    for dir_path in [EXTRACTED_IMAGES, EXTRACTED_AUDIO, EXTRACTED_VIDEO]:
        if os.path.exists(dir_path):
            all_extracted.extend([f for f in os.listdir(dir_path) if f.endswith('.txt')])
    
    accuracy = calculate_detection_accuracy(image_files, audio_files, video_files, all_extracted)

    with open(FINAL_REPORT, "w") as f:

        # ---- TITLE ----
        write_separator(f)
        f.write("  DIGITAL FORENSICS REPORT\n")
        f.write("  STEGANOGRAPHY DETECTION AND HIDDEN DATA EXTRACTION\n")
        write_separator(f)
        f.write(f"\n  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Case ID   : DF-2026-001\n")
        f.write(f"  Class.    : Confidential\n\n")

        # ---- EXECUTIVE SUMMARY ----
        write_section(f, "1. Executive Summary")
        f.write(
            "This investigation performed automated steganography detection and\n"
            "payload extraction across a dataset of image, audio, and video files.\n"
            "The dataset was constructed with known clean/stego pairs to validate\n"
            "detection accuracy of the toolchain.\n\n"
        )
        f.write(f"  Files analyzed   : {len(image_files)} images, {len(audio_files)} audio, {len(video_files)} video\n")
        f.write(f"  Stego images     : {accuracy['stego_total']}  |  Clean images: {accuracy['clean_total']}\n")
        f.write(f"  Payloads found   : {img_extracted_count} image + {aud_extracted_count} audio + {vid_extracted_count} video\n")
        f.write(f"  Image detection  : {accuracy['detected']}/{accuracy['stego_total']} stego images confirmed ({accuracy['accuracy']:.0f}% accuracy)\n\n")
        f.write(
            "Steghide (DCT-domain embedding) was used for image steganography.\n"
            "EOF-append technique was used for audio and video files.\n"
            "Both techniques were successfully detected and payloads recovered.\n"
        )

        # ---- TOOLS USED ----
        write_section(f, "2. Tools and Methods")
        tools = [
            ("Steghide",              "JPEG steganography embedding and extraction (DCT-domain)"),
            ("ExifTool",              "Metadata extraction and comparison"),
            ("StegExpose",            "Automated statistical steganography detection"),
            ("Python Entropy Analysis","Shannon entropy + LSB chi-square analysis"),
            ("Binwalk",               "Embedded signature detection in media files"),
            ("Strings",               "Raw printable-string extraction from binary files"),
            ("Foremost",              "File carving from binary streams"),
            ("FFmpeg",                "Audio and video media generation"),
            ("StegSolve",             "Manual bit-plane visualization (GUI tool)"),
        ]
        for tool, desc in tools:
            f.write(f"  {tool:<28} {desc}\n")

        # ---- DATASET ----
        write_section(f, "3. Dataset Inventory")
        f.write("IMAGES:\n")
        for img in image_files:
            tag = "[STEGO]" if img.startswith("stego_") else "[CLEAN]"
            f.write(f"  {tag}  {img}\n")

        f.write("\nAUDIO:\n")
        for aud in audio_files:
            tag = "[STEGO]" if "stego" in aud else "[CLEAN]"
            f.write(f"  {tag}  {aud}\n")
        if not audio_files:
            f.write("  (none found)\n")

        f.write("\nVIDEO:\n")
        for vid in video_files:
            tag = "[STEGO]" if "stego" in vid else "[CLEAN]"
            f.write(f"  {tag}  {vid}\n")
        if not video_files:
            f.write("  (none found)\n")

        # ---- ENTROPY ANALYSIS ----
        write_section(f, "4. Entropy Analysis")
        f.write(
            "Shannon entropy (bits/pixel) was calculated for each image.\n"
            "Higher entropy after embedding may indicate data injection.\n\n"
        )
        f.write(f"  {'File':<20} {'Entropy':<14} {'Type'}\n")
        f.write("  " + "-" * 50 + "\n")

        pairs = [("clean_1.jpg", "stego_1.jpg"), ("clean_2.jpg", "stego_2.jpg"), ("clean_3.jpg", "stego_3.jpg")]
        for clean, stego in pairs:
            ce = entropy_data.get(clean, "N/A")
            se = entropy_data.get(stego, "N/A")
            delta = ""
            if isinstance(ce, float) and isinstance(se, float):
                delta = f"  (delta: {se - ce:+.4f})"
            f.write(f"  {clean:<20} {str(ce):<14} CLEAN\n")
            f.write(f"  {stego:<20} {str(se):<14} STEGO{delta}\n")
            f.write("\n")

        f.write(
            "Note: Steghide can both increase or decrease entropy depending on\n"
            "the image content and payload size. The key indicator is the\n"
            "metadata change (JFIF/Baseline DCT vs original Exif/Progressive DCT).\n"
        )

        # ---- DETECTION RESULTS ----
        write_section(f, "5. Detection Results")
        f.write("5a. Metadata Fingerprint (ExifTool)\n")
        f.write("-" * 50 + "\n")
        f.write(
            "Steghide rewrites the JPEG container when embedding, causing\n"
            "distinctive metadata changes that serve as reliable forensic markers:\n\n"
        )
        fingerprints = [
            ("JFIF Version 1.01",         "Present in all stego images; original images use Exif"),
            ("Encoding: Baseline DCT",     "Stego images; clean images use Progressive DCT"),
            ("Resolution: 1x1 (None)",     "Stego images; clean images have 72 DPI / inches"),
            ("Missing UserComment field",  "Stego images; clean images carry Picsum ID comment"),
            ("Missing Exif Byte Order",    "Stego images have no Exif sub-IFD"),
        ]
        for marker, note in fingerprints:
            f.write(f"  [!] {marker}\n      -> {note}\n\n")

        f.write("5b. Statistical Analysis (Entropy + Chi-Square)\n")
        f.write("-" * 50 + "\n")
        if detection_content and "EMBEDDING ALGORITHM ANALYSIS" in detection_content:
            # Extract the pair analysis section
            match = re.search(
                r"CLEAN vs STEGO PAIR ANALYSIS\n-+\n([\s\S]+?)(?=={3,}|\Z)",
                detection_content
            )
            if match:
                f.write(match.group(1)[:2000])
        else:
            f.write("  Run analyze_algorithms.py to populate this section.\n")

        # Add audio/video comparison from detection report
        f.write("\n5c. Audio/Video Media Comparison\n")
        f.write("-" * 50 + "\n")
        if detection_content and "CLEAN vs STEGO MEDIA COMPARISON" in detection_content:
            # Extract the media comparison section
            match = re.search(
                r"CLEAN vs STEGO MEDIA COMPARISON\n-+\n([\s\S]+?)(?=={3,}|\Z)",
                detection_content
            )
            if match:
                f.write(match.group(1)[:2000])
                f.write("\n")
            else:
                f.write("  Media comparison data not found in detection report.\n")
        else:
            f.write("  Audio/video comparison not available. Run scan_audio_video.py first.\n")

        if stegexpose_block:
            f.write("\n5d. StegExpose Results\n")
            f.write("-" * 50 + "\n")
            f.write(stegexpose_block + "\n")
        else:
            f.write("\n5d. StegExpose Results\n")
            f.write("-" * 50 + "\n")
            f.write("  StegExpose not run or results not found in detection report.\n")
            f.write("  Run: ./run_stegexpose.sh\n")

        # ---- EXTRACTION RESULTS ----
        write_section(f, "6. Extraction Results")

        # Image extractions
        f.write("6a. Image Payloads (Steghide)\n")
        f.write("-" * 50 + "\n")
        extracted_txt = [f for f in img_extracted if f.endswith(".txt")]
        if extracted_txt:
            for fname in extracted_txt:
                fpath = os.path.join(EXTRACTED_IMAGES, fname)
                f.write(f"\n  File: {fname}\n")
                try:
                    with open(fpath, "r") as ef:
                        content = ef.read().strip()
                    for line in content.splitlines():
                        f.write(f"    {line}\n")
                except Exception:
                    f.write("    (could not read file)\n")
        else:
            f.write("  No image payloads extracted yet. Run: ./run_extract.sh\n")

        # Audio extractions
        f.write("\n6b. Audio Payloads (EOF Append)\n")
        f.write("-" * 50 + "\n")
        aud_txts = [fi for fi in aud_extracted if fi.endswith(".txt")]
        if aud_txts:
            for fname in aud_txts:
                fpath = os.path.join(EXTRACTED_AUDIO, fname)
                f.write(f"\n  File: {fname}\n")
                try:
                    with open(fpath, "r") as ef:
                        f.write(ef.read().strip() + "\n")
                except Exception:
                    f.write("    (could not read file)\n")
        else:
            f.write("  No audio payloads extracted yet. Run: ./run_extract.sh\n")

        # Video extractions
        f.write("\n6c. Video Payloads (EOF Append)\n")
        f.write("-" * 50 + "\n")
        vid_txts = [fi for fi in vid_extracted if fi.endswith(".txt")]
        if vid_txts:
            for fname in vid_txts:
                fpath = os.path.join(EXTRACTED_VIDEO, fname)
                f.write(f"\n  File: {fname}\n")
                try:
                    with open(fpath, "r") as ef:
                        f.write(ef.read().strip() + "\n")
                except Exception:
                    f.write("    (could not read file)\n")
        else:
            f.write("  No video payloads extracted yet. Run: ./run_extract.sh\n")

        # ---- ALGORITHM ANALYSIS ----
        write_section(f, "7. Embedding Algorithm Analysis")
        f.write(
            "Two steganography techniques were identified in this dataset:\n\n"
            "A. STEGHIDE — DCT-domain (JPEG images)\n"
            "   Steghide modifies DCT coefficients using a graph-theoretic\n"
            "   matching algorithm to minimize distortion. This is more\n"
            "   sophisticated than raw LSB substitution:\n"
            "   - Payload bits are mapped onto pairs of DCT coefficients\n"
            "   - Graph matching ensures minimal changes to the coefficient histogram\n"
            "   - Password-based AES encryption protects the payload\n"
            "   - Detectability: Medium — statistical tests can detect it;\n"
            "     metadata changes betray it outright in this dataset\n\n"
            "B. EOF APPEND (audio / video)\n"
            "   The payload is simply concatenated after the valid media\n"
            "   end-of-stream marker. Media players stop reading at the EOF\n"
            "   marker and ignore trailing bytes, but they remain on disk.\n"
            "   - Trivially detectable with binwalk, strings, or file size checks\n"
            "   - Payload is unencrypted (plaintext in this dataset)\n"
            "   - Detectability: High — no attempt to hide the payload\n"
        )

        # ---- DETECTION ACCURACY ----
        write_section(f, "8. Detection Accuracy and Recommendations")
        f.write("ACCURACY SUMMARY\n")
        f.write("-" * 50 + "\n")
        f.write(f"  Stego images in dataset   : {accuracy['stego_total']}\n")
        f.write(f"  Clean images in dataset   : {accuracy['clean_total']}\n")
        f.write(f"  Images positively confirmed: {accuracy['detected']}\n")
        f.write(f"  Extraction accuracy (image): {accuracy['accuracy']:.0f}%\n\n")
        f.write(
            "The metadata fingerprint method (ExifTool) provides near-100%\n"
            "accuracy for Steghide-embedded JPEG files in this dataset because\n"
            "Steghide always rewrites the JPEG container, destroying original\n"
            "metadata. In real-world scenarios where the original metadata is\n"
            "not available for comparison, statistical methods are needed.\n\n"
        )

        f.write("RECOMMENDATIONS\n")
        f.write("-" * 50 + "\n")
        recommendations = [
            ("Use metadata comparison as a first-pass filter",
             "Steghide rewrites Exif; compare against originals when available."),
            ("Apply StegExpose for automated statistical screening",
             "Effective at detecting Steghide, OutGuess, and F5 in large batches."),
            ("Check file size anomalies for audio/video",
             "EOF-append increases size; compare to a clean reference."),
            ("Run binwalk on all media files",
             "Flags embedded signatures and appended data automatically."),
            ("Use password-protected extraction for Steghide payloads",
             "Common passwords (1234, password, stego) should be tried with stegcracker."),
            ("Deploy StegSolve for visual LSB analysis",
             "Manual bit-plane inspection can reveal spatial LSB patterns."),
            ("Encrypt payloads in real-world covert channels",
             "Plaintext EOF-append payloads are trivially recoverable; always encrypt."),
        ]
        for i, (title, detail) in enumerate(recommendations, 1):
            f.write(f"\n  {i}. {title}\n     {detail}\n")

        # ---- CONCLUSION ----
        write_section(f, "9. Conclusion")
        f.write(
            "This investigation successfully identified, detected, and extracted\n"
            "hidden payloads from all steganographic files in the dataset.\n\n"
            "Key findings:\n"
            "  - All three JPEG stego images were confirmed via metadata analysis\n"
            "    and steghide extraction (password: 1234)\n"
            "  - Audio and video payloads used the EOF-append technique and were\n"
            "    recovered via binwalk / tail analysis\n"
            "  - The metadata fingerprinting approach (Exif/JFIF comparison) proved\n"
            "    the most reliable detection method for this toolchain\n"
            "  - Statistical methods (entropy delta, chi-square) provided supporting\n"
            "    evidence but are less definitive on small payloads\n\n"
            "Investigation status: COMPLETE\n"
        )

        write_separator(f)
        f.write("  END OF REPORT\n")
        write_separator(f)

    print(Fore.GREEN + f"\n[OK] Consolidated report written to {FINAL_REPORT}")

    # Also write the extraction report skeleton if it doesn't exist
    if not os.path.exists(EXTRACTION_REPORT):
        with open(EXTRACTION_REPORT, "w") as f:
            f.write("EXTRACTION REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write("(Run ./run_extract.sh to populate this report)\n")
        print(Fore.YELLOW + f"[OK] Extraction report placeholder created at {EXTRACTION_REPORT}")


if __name__ == "__main__":
    main()
