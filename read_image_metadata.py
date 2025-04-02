import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import json

# Specify the exact image path
image_path = r"C:\Users\felix\ml\ComfyUI\output\Generator\Canny-Multiply_00068_.png"

# Function to read metadata from the image and return it as a string
def read_image_metadata(image_path):
    metadata_output = f"\nProcessing: {image_path}\n"
    try:
        with Image.open(image_path) as img:
            # 1. Check EXIF data (unlikely for PNG, but included for completeness)
            exif_data = img._getexif()
            if exif_data:
                metadata_output += "EXIF Data Found:\n"
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    metadata_output += f"  {tag_name}: {value}\n"
            else:
                metadata_output += "No EXIF data found.\n"

            # 2. Check PNG metadata (text chunks)
            if hasattr(img, 'info'):
                metadata_output += "PNG Info Found:\n"
                for key, value in img.info.items():
                    metadata_output += f"  {key}: {value}\n"
                    # If the value looks like JSON, try parsing it
                    if isinstance(value, str) and ("{" in value or "[" in value):
                        try:
                            parsed_json = json.loads(value)
                            metadata_output += f"    Parsed JSON: {json.dumps(parsed_json, indent=2)}\n"
                        except json.JSONDecodeError:
                            metadata_output += "    Could not parse as JSON.\n"
            else:
                metadata_output += "No PNG info found.\n"

    except Exception as e:
        metadata_output += f"Error processing {image_path}: {e}\n"
    
    return metadata_output

# Function to write metadata to a text file
def write_metadata_to_file(metadata, filename="image_metadata.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(metadata)
        print(f"Metadata exported to {filename} successfully!")
    except Exception as e:
        print(f"Error writing to file: {e}")

# Run the script for the single image
if __name__ == "__main__":
    print(f"Scanning metadata for {image_path}...")
    if os.path.exists(image_path):
        metadata = read_image_metadata(image_path)
        write_metadata_to_file(metadata, "image_metadata.txt")
    else:
        print(f"Image {image_path} does not exist!")
    print("\nScan complete!")