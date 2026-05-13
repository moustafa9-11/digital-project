import os
import subprocess
import math
from colorama import Fore, init

init(autoreset=True)

AUDIO_DIR = "datasets/audio"
VIDEO_DIR = "datasets/videos"
REPORT_FILE = "reports/detection_report.txt"


def get_file_size(path):
    return os.path.getsize(path)


def run_binwalk(file_path):
    try:
        result = subprocess.run(
            ["binwalk", file_path],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"binwalk error: {e}"


def run_strings_check(file_path):
    try:
        result = subprocess.run(
            ["strings", file_path],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().splitlines()
        readable = [l for l in lines if len(l) > 6]
        return "\n".join(readable[:30]) if readable else "No significant strings found."
    except Exception as e:
        return f"strings error: {e}"


def check_appended_data(file_path, _=None):
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        # Scan last 4KB more thoroughly for meaningful plaintext
        tail = data[-4096:]
        
        # First pass: look for obvious plaintext lines
        lines = tail.split(b"\n")
        found = []
        for line in lines:
            try:
                decoded = line.decode("ascii").strip()
                if len(decoded) > 6 and decoded.isprintable():
                    found.append(decoded)
            except UnicodeDecodeError:
                continue
        
        # Second pass: look for specific payload patterns that might be mixed with binary
        # Handle case where payload is embedded in binary data
        try:
            # Try to decode with error replacement and look for meaningful patterns
            tail_text = tail.decode("utf-8", errors="replace")
            
            # Look for specific payload indicators
            # Check for actual hidden payloads first
            # Use more specific indicators to avoid false positives with video metadata
            hidden_payload_indicators = ["Hidden", "payload", "secret", "message"]
            # Only check for "data" if it's part of a meaningful phrase
            data_phrases = ["Hidden data", "secret data", "message data"]
            has_hidden_payload = any(indicator in tail_text for indicator in hidden_payload_indicators)
            has_data_payload = any(phrase in tail_text for phrase in data_phrases)
            
            if has_hidden_payload or has_data_payload:
                # Found actual hidden payload - extract it
                all_indicators = hidden_payload_indicators + data_phrases
                for indicator in all_indicators:
                    if indicator in tail_text:
                        # Extract surrounding context
                        start = tail_text.rfind(indicator) - 50
                        if start < 0:
                            start = 0
                        end = tail_text.rfind(indicator) + 100
                        if end > len(tail_text):
                            end = len(tail_text)
                        context = tail_text[start:end].strip()
                        if len(context) > 10:
                            found.append(f"DETECTED: {context}")
                            break
            else:
                # No hidden payload found, check if it's just video metadata
                video_metadata_patterns = ['!hdlr', 'mdirappl', '-ilst', 'data\x00\x00\x00\x01', 'Lavf', 'Lavc', 'libx264', 'libx265']
                is_video_metadata = any(pattern in tail_text for pattern in video_metadata_patterns)
                
                if is_video_metadata:
                    # This is just video metadata, not steganography
                    pass  # Don't add to found array
                else:
                    # Check for other potential indicators
                    for indicator in hidden_payload_indicators:
                        if indicator in tail_text:
                            start = tail_text.rfind(indicator) - 50
                            if start < 0:
                                start = 0
                            end = tail_text.rfind(indicator) + 100
                            if end > len(tail_text):
                                end = len(tail_text)
                            context = tail_text[start:end].strip()
                            if len(context) > 10:
                                found.append(f"DETECTED: {context}")
                                break
        except:
            pass
        
        # Third pass: scan for consecutive printable characters (potential payload)
        # But be more selective - ignore MP3 padding patterns
        consecutive_printable = ""
        max_consecutive = ""
        for byte in tail:
            if 32 <= byte <= 126:  # Printable ASCII range
                consecutive_printable += chr(byte)
            else:
                if len(consecutive_printable) > len(max_consecutive):
                    max_consecutive = consecutive_printable
                consecutive_printable = ""
        
        # Check the last sequence too
        if len(consecutive_printable) > len(max_consecutive):
            max_consecutive = consecutive_printable
            
        # If we found a significant printable sequence, add it
        # But only if it's not just MP3 padding or common binary artifacts
        if len(max_consecutive) > 20:  # Increased threshold
            # Skip if it's mostly repetitive characters (like UUUUU padding)
            unique_chars = set(max_consecutive.lower())
            
            # More strict filtering for MP3 padding and video container metadata
            # Skip if: mostly U characters, contains LAME metadata, or is just padding
            # Also skip normal video container metadata
            video_metadata_indicators = ['hdlr', 'mdirappl', '-ilst', 'Lavf', 'Lavc', 'libx264', 'libx265']
            is_video_metadata = any(indicator in max_consecutive for indicator in video_metadata_indicators)
            
            if (len(unique_chars) > 3 and 
                not max_consecutive.strip().startswith('uuuu') and
                'LAME' not in max_consecutive and
                not is_video_metadata and
                max_consecutive.count('U') / len(max_consecutive) < 0.7):  # Less than 70% U characters
                found.append(f"CONSECUTIVE: {max_consecutive}")

        if found:
            return "SUSPICIOUS: Readable text found near EOF:\n" + "\n".join(found)
        return "No appended data detected in EOF region."
    except Exception as e:
        return f"Appended data check error: {e}"


def calculate_entropy_bytes(file_path):
    """Calculate Shannon entropy of raw file bytes."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        if not data:
            return 0.0
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        total = len(data)
        entropy = 0.0
        for count in freq:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        return round(entropy, 6)
    except Exception as e:
        return f"Entropy error: {e}"


def run_exiftool(file_path):
    try:
        result = subprocess.run(
            ["exiftool", file_path],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"exiftool error: {e}"


def scan_file(file_path, file_type, report):
    filename = os.path.basename(file_path)
    size = get_file_size(file_path)
    entropy = calculate_entropy_bytes(file_path)

    print(Fore.CYAN + f"  Scanning {filename} ({size} bytes, entropy: {entropy})")

    report.write(f"\nFILE: {filename} [{file_type.upper()}]\n")
    report.write("-" * 50 + "\n")
    report.write(f"File Size   : {size} bytes\n")
    report.write(f"Byte Entropy: {entropy}\n\n")

    report.write("[APPENDED DATA CHECK]\n")
    appended = check_appended_data(file_path, None)
    report.write(appended + "\n\n")

    report.write("[BINWALK ANALYSIS]\n")
    binwalk_out = run_binwalk(file_path)
    report.write(binwalk_out if binwalk_out.strip() else "No embedded signatures found.\n")
    report.write("\n")

    report.write("[STRINGS ANALYSIS (top 30 readable strings)]\n")
    strings_out = run_strings_check(file_path)
    report.write(strings_out + "\n\n")

    report.write("[EXIF / METADATA]\n")
    exif_out = run_exiftool(file_path)
    report.write(exif_out if exif_out.strip() else "No metadata found.\n")
    report.write("\n")


def compare_media_pairs(report):
    pairs = [
        ("datasets/audio/clean_audio.mp3",  "datasets/audio/stego_audio.mp3"),
        ("datasets/videos/clean_video.mp4", "datasets/videos/stego_video.mp4"),
    ]
    report.write("\nCLEAN vs STEGO MEDIA COMPARISON\n")
    report.write("-" * 50 + "\n")
    for clean_path, stego_path in pairs:
        if not (os.path.exists(clean_path) and os.path.exists(stego_path)):
            continue
        c_size = os.path.getsize(clean_path)
        s_size = os.path.getsize(stego_path)
        c_entropy = calculate_entropy_bytes(clean_path)
        s_entropy = calculate_entropy_bytes(stego_path)
        name = os.path.basename(stego_path)
        report.write(f"\n{os.path.basename(clean_path)} vs {name}\n")
        report.write(f"  Size    : clean={c_size} B  stego={s_size} B  delta={s_size - c_size:+d} B\n")
        report.write(f"  Entropy : clean={c_entropy}  stego={s_entropy}  delta={s_entropy - c_entropy:+.6f}\n")
        if s_size > c_size:
            report.write(f"  -> SUSPICIOUS: stego file is {s_size - c_size} bytes larger\n")

def main():
    with open(REPORT_FILE, "a") as report:

        report.write("\n\n" + "=" * 60 + "\n")
        report.write("AUDIO / VIDEO STEGANOGRAPHY SCAN\n")
        report.write("=" * 60 + "\n")

        # --- Audio ---
        print(Fore.YELLOW + "\n[+] Scanning audio files...")
        if os.path.isdir(AUDIO_DIR):
            audio_files = [
                f for f in os.listdir(AUDIO_DIR)
                if f.lower().endswith((".mp3", ".wav", ".ogg", ".flac"))
            ]
            if audio_files:
                for f in audio_files:
                    scan_file(os.path.join(AUDIO_DIR, f), "audio", report)
            else:
                print(Fore.RED + "  No audio files found in " + AUDIO_DIR)
                report.write("No audio files found.\n")
        else:
            print(Fore.RED + f"  Directory not found: {AUDIO_DIR}")
            report.write(f"Audio directory not found: {AUDIO_DIR}\n")

        # --- Video ---
        print(Fore.YELLOW + "\n[+] Scanning video files...")

        if os.path.isdir(VIDEO_DIR):
            video_files = [
                f for f in os.listdir(VIDEO_DIR)
                if f.lower().endswith((".mp4", ".avi", ".mkv", ".mov"))
            ]
            if video_files:
                for f in video_files:
                    scan_file(os.path.join(VIDEO_DIR, f), "video", report)
            else:
                print(Fore.RED + "  No video files found in " + VIDEO_DIR)
                report.write("No video files found.\n")
        else:
            print(Fore.RED + f"  Directory not found: {VIDEO_DIR}")
            report.write(f"Video directory not found: {VIDEO_DIR}\n")

        compare_media_pairs(report)

    print(Fore.GREEN + "\n[OK] Audio/video scan complete. Results appended to detection_report.txt")


if __name__ == "__main__":
    main()
