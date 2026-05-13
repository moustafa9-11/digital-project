import os
import math
import json
from PIL import Image
import numpy as np
from colorama import Fore, init

init(autoreset=True)

IMAGE_DIR = "datasets/images"
REPORT_FILE = "reports/detection_report.txt"

# Known clean/stego pairs based on project naming convention
PAIRS = [
    ("clean_1.jpg", "stego_1.jpg"),
    ("clean_2.jpg", "stego_2.jpg"),
    ("clean_3.jpg", "stego_3.jpg"),
]

ALGORITHM_NOTES = {
    "steghide": {
        "name": "Steghide (DCT-domain / graph-theoretic LSB)",
        "description": (
            "Steghide embeds data in the DCT (Discrete Cosine Transform) "
            "coefficients of JPEG images using a graph-theoretic algorithm. "
            "Rather than simple LSB substitution, it modifies DCT coefficients "
            "to encode payload bits while preserving the statistical distribution "
            "of the cover image as closely as possible."
        ),
        "detection_indicators": [
            "Subtle entropy increase in the modified image",
            "Chi-square attack on LSB distribution can reveal patterns",
            "File size may increase slightly versus original JPEG",
            "JFIF metadata vs Exif metadata discrepancy (stego files lose Exif)",
            "StegExpose score exceeds threshold (default 0.2)",
        ],
        "artifacts": [
            "JFIF 1.01 header replaces original Exif (visible in ExifTool output)",
            "Baseline DCT replaces Progressive DCT encoding",
            "Resolution metadata stripped (X/Y resolution set to 1, unit: None)",
            "UserComment and Picsum ID fields are removed",
        ],
    },
    "appended": {
        "name": "EOF Append (raw payload concatenation)",
        "description": (
            "The simplest steganography technique: a payload is appended "
            "directly after the valid end-of-file marker of the media container. "
            "The player or viewer ignores the trailing bytes, but they persist "
            "on disk and can be trivially recovered with binwalk, strings, or dd."
        ),
        "detection_indicators": [
            "File size larger than expected for a clean media file",
            "Binwalk detects multiple signatures / reports data after EOF",
            "Strings command returns readable text in the EOF region",
            "Hex editor reveals non-zero data past the media end marker",
        ],
        "artifacts": [
            "Payload is in plaintext — no encryption or obfuscation",
            "Easily recoverable with: tail -c N file or dd skip=X",
            "No impact on visual/audio quality of the carrier",
        ],
    },
}


def calculate_entropy(image_path):
    """Shannon entropy of grayscale pixel values."""
    img = Image.open(image_path).convert("L")
    histogram = img.histogram()
    total = sum(histogram)
    probs = [h / total for h in histogram if h != 0]
    return -sum(p * math.log2(p) for p in probs)


def lsb_plane_analysis(image_path):
    """
    Analyze the LSB plane of an image.
    A clean image has a roughly 50/50 distribution of 0/1 LSBs.
    A steghide-modified image will have a slightly skewed distribution
    due to coefficient adjustments.
    Returns: (lsb_0_ratio, lsb_1_ratio, chi_square_score)
    """
    img = Image.open(image_path).convert("L")
    pixels = np.array(img).flatten()

    lsb = pixels & 1
    n0 = np.sum(lsb == 0)
    n1 = np.sum(lsb == 1)
    total = len(lsb)

    r0 = n0 / total
    r1 = n1 / total

    # Chi-square statistic: expected 50/50 under H0 (no hidden data)
    expected = total / 2
    chi2 = ((n0 - expected) ** 2 + (n1 - expected) ** 2) / expected

    return r0, r1, chi2


def compare_pair(clean_path, stego_path):
    clean_entropy = calculate_entropy(clean_path)
    stego_entropy = calculate_entropy(stego_path)
    delta_entropy = stego_entropy - clean_entropy

    clean_r0, clean_r1, clean_chi2 = lsb_plane_analysis(clean_path)
    stego_r0, stego_r1, stego_chi2 = lsb_plane_analysis(stego_path)

    clean_size = os.path.getsize(clean_path)
    stego_size = os.path.getsize(stego_path)

    return {
        "clean_entropy": round(clean_entropy, 6),
        "stego_entropy": round(stego_entropy, 6),
        "delta_entropy": round(delta_entropy, 6),
        "clean_lsb": (round(clean_r0, 4), round(clean_r1, 4)),
        "stego_lsb": (round(stego_r0, 4), round(stego_r1, 4)),
        "clean_chi2": round(clean_chi2, 4),
        "stego_chi2": round(stego_chi2, 4),
        "clean_size": clean_size,
        "stego_size": stego_size,
        "size_delta": stego_size - clean_size,
    }


def interpret_result(metrics):
    indicators = []

    if abs(metrics["delta_entropy"]) > 0.01:
        direction = "increase" if metrics["delta_entropy"] > 0 else "decrease"
        indicators.append(
            f"Entropy {direction} of {abs(metrics['delta_entropy']):.4f} bits — "
            "consistent with DCT coefficient modification"
        )
    else:
        indicators.append(
            "Entropy delta minimal — embedding may be sparse or well-camouflaged"
        )

    if metrics["stego_chi2"] > metrics["clean_chi2"] * 1.5:
        indicators.append(
            f"Chi-square score elevated ({metrics['stego_chi2']:.2f} vs "
            f"{metrics['clean_chi2']:.2f}) — LSB distribution shift detected"
        )
    else:
        indicators.append(
            "Chi-square scores similar — LSB distribution largely preserved"
        )

    if metrics["size_delta"] != 0:
        indicators.append(
            f"File size changed by {metrics['size_delta']:+d} bytes after embedding"
        )

    return indicators


def write_report(report, pairs_results):
    report.write("\n\n" + "=" * 60 + "\n")
    report.write("EMBEDDING ALGORITHM ANALYSIS\n")
    report.write("=" * 60 + "\n\n")

    # --- Algorithm Explanations ---
    report.write("ALGORITHMS DETECTED IN THIS DATASET\n")
    report.write("-" * 50 + "\n\n")

    for algo_key, algo in ALGORITHM_NOTES.items():
        report.write(f"[{algo['name']}]\n\n")
        report.write(f"Description:\n{algo['description']}\n\n")

        report.write("Detection indicators:\n")
        for ind in algo["detection_indicators"]:
            report.write(f"  - {ind}\n")

        report.write("\nForensic artifacts in this dataset:\n")
        for art in algo["artifacts"]:
            report.write(f"  * {art}\n")

        report.write("\n")

    # --- Pair Comparisons ---
    report.write("-" * 50 + "\n")
    report.write("CLEAN vs STEGO PAIR ANALYSIS\n")
    report.write("-" * 50 + "\n\n")

    for clean_name, stego_name, metrics in pairs_results:

        report.write(f"Pair: {clean_name}  <->  {stego_name}\n")
        report.write(
            f"  Entropy  : clean={metrics['clean_entropy']:.6f}  "
            f"stego={metrics['stego_entropy']:.6f}  "
            f"delta={metrics['delta_entropy']:+.6f}\n"
        )
        report.write(
            f"  LSB dist : clean=({metrics['clean_lsb'][0]:.4f}/{metrics['clean_lsb'][1]:.4f})  "
            f"stego=({metrics['stego_lsb'][0]:.4f}/{metrics['stego_lsb'][1]:.4f})\n"
        )
        report.write(
            f"  Chi2     : clean={metrics['clean_chi2']:.2f}  "
            f"stego={metrics['stego_chi2']:.2f}\n"
        )
        report.write(
            f"  File size: clean={metrics['clean_size']} B  "
            f"stego={metrics['stego_size']} B  "
            f"delta={metrics['size_delta']:+d} B\n"
        )

        report.write("  Interpretation:\n")
        for interp in interpret_result(metrics):
            report.write(f"    -> {interp}\n")

        report.write("\n")


def main():
    pairs_results = []

    print(Fore.CYAN + "\n[+] Analyzing clean vs stego image pairs...")

    for clean_name, stego_name in PAIRS:
        clean_path = os.path.join(IMAGE_DIR, clean_name)
        stego_path = os.path.join(IMAGE_DIR, stego_name)

        if not os.path.exists(clean_path):
            print(Fore.RED + f"  Missing: {clean_path}")
            continue
        if not os.path.exists(stego_path):
            print(Fore.RED + f"  Missing: {stego_path}")
            continue

        print(Fore.YELLOW + f"  Comparing {clean_name} <-> {stego_name}")
        metrics = compare_pair(clean_path, stego_path)
        pairs_results.append((clean_name, stego_name, metrics))

        delta_str = f"{metrics['delta_entropy']:+.6f}"
        print(Fore.GREEN + f"    Entropy delta: {delta_str}  |  Chi2: {metrics['stego_chi2']:.2f}  |  Size delta: {metrics['size_delta']:+d}B")

    with open(REPORT_FILE, "a") as report:
        write_report(report, pairs_results)

    print(Fore.GREEN + "\n[OK] Algorithm analysis complete. Results appended to detection_report.txt")


if __name__ == "__main__":
    main()
