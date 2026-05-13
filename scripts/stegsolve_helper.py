import os
import subprocess

IMAGE_DIR = "datasets/stego/images"

for file in os.listdir(IMAGE_DIR):

    image_path = os.path.join(IMAGE_DIR, file)

    print(f"Opening {file} in StegSolve...")

    subprocess.run([
        "java",
        "-jar",
        "tools/stegsolve.jar",
        image_path
    ])
