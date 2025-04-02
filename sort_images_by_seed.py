import os
import json
from PIL import Image
import shutil

# Specify the directory containing your images
input_folder = r"C:\Users\felix\ml\ComfyUI\output\Generator"

# Function to extract the seed from an image's metadata
def extract_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            # Check PNG info (not EXIF, since PNGs use text chunks)
            if hasattr(img, 'info') and "prompt" in img.info:
                prompt_data = img.info["prompt"]
                # If prompt_data is already a dict, no need to parse
                if isinstance(prompt_data, str):
                    try:
                        metadata = json.loads(prompt_data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse prompt metadata in {image_path}")
                        return None
                elif isinstance(prompt_data, dict):
                    metadata = prompt_data
                else:
                    print(f"Prompt metadata in {image_path} is not a string or dict")
                    return None

                # Look for the "Seed Everywhere" node in the metadata
                for node_id, node in metadata.items():
                    if isinstance(node, dict) and node.get("class_type") == "Seed Everywhere":
                        seed = node["inputs"].get("seed")
                        if seed:
                            return str(seed)
                print(f"No 'Seed Everywhere' node found in metadata for {image_path}")
                return None
            else:
                print(f"No 'prompt' metadata found in {image_path}")
                return None
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

# Function to sort images into folders based on seed
def sort_images_by_seed():
    # Ensure the input folder exists
    if not os.path.exists(input_folder):
        print(f"Input folder {input_folder} does not exist!")
        return

    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        
        # Check if it's an image file
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            seed = extract_metadata(file_path)
            if seed:
                # Create a destination folder based on the seed value
                seed_folder = os.path.join(input_folder, f"Seed_{seed}")
                os.makedirs(seed_folder, exist_ok=True)
                
                # Move the image to the seed folder
                destination_path = os.path.join(seed_folder, filename)
                shutil.move(file_path, destination_path)
                print(f"Moved {filename} to {seed_folder}")
            else:
                print(f"Skipping {filename} - no seed found")

# Run the script
if __name__ == "__main__":
    print(f"Starting to sort images in {input_folder}")
    sort_images_by_seed()
    print("Sorting complete!")