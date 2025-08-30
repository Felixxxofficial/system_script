import os
import re
import random
import shutil

def get_existing_img_numbers(folder_path):
    """Get set of existing IMG_XXXX numbers in the folder."""
    existing_numbers = set()
    img_pattern = re.compile(r'IMG_(\d{4})\.(jpg|jpeg|png)', re.IGNORECASE)
    for filename in os.listdir(folder_path):
        match = img_pattern.match(filename)
        if match:
            existing_numbers.add(int(match.group(1)))
    return existing_numbers

def generate_unique_img_number(existing_numbers):
    """Generate a unique IMG number that doesn't exist in the folder."""
    while True:
        img_number = random.randint(1, 9999)
        if img_number not in existing_numbers:
            return img_number

def process_image_file(image_path, folder_path, existing_numbers):
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        return
    filename = os.path.basename(image_path)
    # Skip files already named IMG_XXXX
    if filename.startswith('IMG_'):
        print(f"Skipping already renamed: {filename}")
        return
    # Generate unique IMG_XXXX filename
    img_number = generate_unique_img_number(existing_numbers)
    new_filename = f"IMG_{img_number:04d}{ext}"
    new_path = os.path.join(folder_path, new_filename)
    # Ensure no collision
    while os.path.exists(new_path):
        img_number = generate_unique_img_number(existing_numbers)
        new_filename = f"IMG_{img_number:04d}{ext}"
        new_path = os.path.join(folder_path, new_filename)
    print(f"Renaming {filename} -> {new_filename}")
    shutil.move(image_path, new_path)
    existing_numbers.add(img_number)

def process_threads_subfolders(base_folder):
    threads_folder = os.path.join(base_folder, 'Threads')
    if not os.path.exists(threads_folder):
        print(f"No Threads folder in: {base_folder}")
        return
    for subfolder in os.listdir(threads_folder):
        subfolder_path = os.path.join(threads_folder, subfolder)
        if os.path.isdir(subfolder_path):
            image_files = [f for f in os.listdir(subfolder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not image_files:
                continue
            print(f"\nProcessing folder: {subfolder_path}")
            existing_numbers = get_existing_img_numbers(subfolder_path)
            for filename in image_files:
                full_path = os.path.join(subfolder_path, filename)
                process_image_file(full_path, subfolder_path, existing_numbers)

def main():
    # List of main category folders to process
    base_folders = [
        r"C:\Users\felix\OFM\Reels\Images\Student",
        r"C:\Users\felix\OFM\Reels\Images\Goth",
        r"C:\Users\felix\OFM\Reels\Images\Nature",
        r"C:\Users\felix\OFM\Reels\Images\Normal",
        r"C:\Users\felix\OFM\Reels\Images\Construction",
        r"C:\Users\felix\OFM\Reels\Images\Gamer"
    ]
    for folder in base_folders:
        if os.path.exists(folder):
            process_threads_subfolders(folder)
        else:
            print(f"Folder does not exist: {folder}")

if __name__ == "__main__":
    main() 