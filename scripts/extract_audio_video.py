import os
import subprocess
from colorama import Fore, init

init(autoreset=True)

AUDIO_DIR = "datasets/audio"
VIDEO_DIR = "datasets/videos"
OUTPUT_AUDIO = "extracted/audio"
OUTPUT_VIDEO = "extracted/videos"
REPORT_FILE = "reports/extraction_report.txt"

os.makedirs(OUTPUT_AUDIO, exist_ok=True)
os.makedirs(OUTPUT_VIDEO, exist_ok=True)


def is_meaningful_payload(content, filename):
    """
    Check if extracted content is a meaningful payload vs just MP3 padding/binary noise.
    Returns True if content appears to be actual hidden data.
    """
    content_lower = content.lower()
    
    # Check for obvious payload indicators FIRST (most reliable)
    payload_keywords = ["hidden", "payload", "secret", "message", "data", "text"]
    if any(keyword in content_lower for keyword in payload_keywords):
        # But make sure it's not just in MP3 metadata/padding
        # Look for actual meaningful sentences
        meaningful_phrases = [
            "hidden audio payload",
            "hidden video payload", 
            "secret message",
            "hidden data"
        ]
        for phrase in meaningful_phrases:
            if phrase in content_lower:
                # Found a meaningful phrase - this is enough to consider it meaningful
                # The presence of these specific phrases indicates actual steganography
                return True
    
    # If no obvious keywords, be very strict about filtering out padding
    lines = content.splitlines()
    meaningful_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Skip extraction header lines
        if (stripped.startswith('Extracted from:') or 
            stripped.startswith('Method:') or 
            stripped.startswith('---')):
            continue
            
        # Skip lines that are mostly 'U' characters (MP3 padding) - very strict
        u_count = stripped.count('U')
        if len(stripped) > 0 and u_count / len(stripped) > 0.3:  # Very low threshold
            continue
            
        # Skip lines with lots of non-printable/binary characters
        printable_count = sum(1 for c in stripped if 32 <= ord(c) <= 126)
        if len(stripped) > 0 and printable_count / len(stripped) < 0.9:  # Very high threshold
            continue
            
        # Skip lines that look like MP3 metadata
        if "LAME" in stripped or "mp3" in stripped.lower():
            continue
            
        # Skip very short lines (likely noise)
        if len(stripped) < 10:  # Increased threshold
            continue
            
        # Skip lines that are mostly repetitive
        unique_chars = set(stripped.lower())
        if len(stripped) > 0 and len(unique_chars) < 4:
            continue
            
        # If we get here, it's potentially meaningful
        meaningful_lines.append(stripped)
    
    # Consider it meaningful only if we have multiple meaningful lines
    # or one substantial meaningful line
    if len(meaningful_lines) == 0:
        return False
    elif len(meaningful_lines) == 1:
        return len(meaningful_lines[0]) > 20  # Increased threshold
    else:
        return True  # Multiple lines suggest real content

def extract_appended_payload(input_path, output_path, media_type):
    """
    Extracts data appended after the valid container end.
    Strategy: use binwalk to locate offset of appended data,
    then dd the tail. Falls back to scanning EOF region for
    readable text.
    """
    filename = os.path.basename(input_path)

    try:
        # Step 1: Use binwalk to find all embedded signatures
        binwalk_result = subprocess.run(
            ["binwalk", "--extract", "--directory", os.path.dirname(output_path), input_path],
            capture_output=True,
            text=True
        )
        binwalk_output = binwalk_result.stdout

        # Step 2: Also try raw tail extraction — our stego files
        # use the simple cat >> method (appended plaintext after EOF)
        with open(input_path, "rb") as f:
            data = f.read()

        # Find the end of valid media container
        # For MP3: last valid sync frame marker is somewhere near the end
        # For MP4: look for the last 'ftyp' or 'moov' atom, then extract after
        # Simple heuristic: scan the last 2KB for readable ASCII payload
        tail = data[-2048:]
        decoded = tail.decode("utf-8", errors="replace")

        readable_lines = []
        for line in decoded.splitlines():
            stripped = line.strip()
            # Accept lines where >70% of chars are printable ASCII
            printable = sum(1 for c in stripped if 32 <= ord(c) < 127)
            if stripped and len(stripped) > 3 and printable / max(len(stripped), 1) > 0.7:
                readable_lines.append(stripped)

        if readable_lines:
            payload = "\n".join(readable_lines)
            
            # Check if this is a meaningful payload vs padding
            if not is_meaningful_payload(payload, filename):
                return False, "No meaningful payload found (only padding/binary noise)"

            with open(output_path, "w") as out:
                out.write(f"Extracted from: {filename}\n")
                out.write(f"Method: EOF tail scan\n")
                out.write("-" * 40 + "\n")
                out.write(payload + "\n")

            return True, f"Payload extracted via EOF tail scan ({len(payload)} bytes)"

        # Step 3: Fallback — try foremost
        foremost_out_dir = os.path.join(
            os.path.dirname(output_path),
            f"foremost_{os.path.splitext(filename)[0]}"
        )
        os.makedirs(foremost_out_dir, exist_ok=True)

        subprocess.run(
            ["foremost", "-i", input_path, "-o", foremost_out_dir, "-q"],
            capture_output=True,
            text=True
        )

        # Check if foremost recovered anything
        found_files = []
        for root, dirs, files in os.walk(foremost_out_dir):
            for f in files:
                if f != "audit.txt":
                    found_files.append(os.path.join(root, f))

        if found_files:
            return True, f"Foremost recovered {len(found_files)} embedded file(s) -> {foremost_out_dir}"

        return False, "No recoverable payload found"

    except Exception as e:
        return False, f"Extraction error: {e}"


def extract_from_directory(src_dir, output_dir, media_type, report):
    extensions = {
        "audio": (".mp3", ".wav", ".ogg", ".flac"),
        "video": (".mp4", ".avi", ".mkv", ".mov"),
    }[media_type]

    if not os.path.isdir(src_dir):
        print(Fore.RED + f"  Directory not found: {src_dir}")
        report.write(f"Directory not found: {src_dir}\n\n")
        return

    files = [f for f in os.listdir(src_dir) if f.lower().endswith(extensions)]

    if not files:
        print(Fore.RED + f"  No {media_type} files found in {src_dir}")
        report.write(f"No {media_type} files found.\n\n")
        return

    for filename in files:
        input_path = os.path.join(src_dir, filename)
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"extracted_{stem}.txt")

        print(Fore.YELLOW + f"  Extracting from {filename}...")

        success, message = extract_appended_payload(input_path, output_path, media_type)

        status = Fore.GREEN + "[FOUND]" if success else Fore.RED + "[NOT FOUND]"
        print(f"  {status} {message}")

        report.write(f"FILE: {filename}\n")
        report.write("-" * 50 + "\n")
        report.write(f"Status  : {'SUCCESS' if success else 'NOT FOUND'}\n")
        report.write(f"Details : {message}\n")

        if success and os.path.exists(output_path):
            report.write(f"Output  : {output_path}\n")
            with open(output_path, "r") as f:
                content = f.read()
            report.write("Payload :\n")
            report.write(content + "\n")

        report.write("\n")


def main():
    with open(REPORT_FILE, "a") as report:

        # Always write the audio/video section header
        report.write("\n\n" + "=" * 60 + "\n")
        report.write("AUDIO / VIDEO EXTRACTION RESULTS\n")
        report.write("=" * 60 + "\n\n")

        print(Fore.CYAN + "\n[+] Extracting from audio files...")
        report.write("--- AUDIO ---\n\n")
        extract_from_directory(AUDIO_DIR, OUTPUT_AUDIO, "audio", report)

        print(Fore.CYAN + "\n[+] Extracting from video files...")
        report.write("--- VIDEO ---\n\n")
        extract_from_directory(VIDEO_DIR, OUTPUT_VIDEO, "video", report)

    print(Fore.GREEN + "\n[OK] Audio/video extraction complete. Results in extraction_report.txt")


if __name__ == "__main__":
    main()
