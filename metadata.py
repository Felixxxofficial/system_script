import exiftool
import os

def extract_all_metadata(image_path):
    # Ensure the file exists
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return

    # Use exiftool to extract all metadata
    try:
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(image_path)[0]  # Returns a dict for the first file
            # Print all metadata in a readable format
            print("\n=== All Metadata ===")
            for key, value in metadata.items():
                print(f"{key}: {value}")
            
            # Save to a text file in the same directory as the image
            output_path = os.path.join(os.path.dirname(image_path), "metadata_output.txt")
            with open(output_path, "w") as f:
                f.write("=== All Metadata ===\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
            print(f"\nMetadata saved to '{output_path}'")
    except Exception as e:
        print(f"Error extracting metadata with exiftool: {e}")

if __name__ == "__main__":
    image_path = r"C:\Users\felix\OFM\Reels\Lightroom\IMG_4071.jpg"
    extract_all_metadata(image_path)