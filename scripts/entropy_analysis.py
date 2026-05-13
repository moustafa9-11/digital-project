from PIL import Image
import numpy as np
import os
import math

IMAGE_DIR = "datasets/images"
REPORT_FILE = "reports/entropy_report.txt"


def calculate_entropy(image_path):

    img = Image.open(image_path).convert("L")

    histogram = img.histogram()

    histogram_length = sum(histogram)

    samples_probability = [
        float(h) / histogram_length
        for h in histogram
        if h != 0
    ]

    entropy = -sum(
        [p * math.log(p, 2) for p in samples_probability]
    )

    return entropy


with open(REPORT_FILE, "w") as report:

    report.write("IMAGE ENTROPY ANALYSIS\n")
    report.write("=" * 60 + "\n\n")

    for image in os.listdir(IMAGE_DIR):

        path = os.path.join(IMAGE_DIR, image)

        entropy = calculate_entropy(path)

        report.write(f"{image} -> Entropy: {entropy}\n")

print("Entropy analysis completed.")
