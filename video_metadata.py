import exiftool
import os

def extract_video_metadata(video_path):
    """
    Extracts and saves metadata from a video file.
    
    Args:
        video_path (str): Path to the video file
    """
    # Ensure the file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return

    # Use exiftool to extract all metadata
    try:
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(video_path)[0]  # Returns a dict for the first file
            
            # Print video-specific metadata in a readable format
            print("\n=== Video Metadata ===")
            print(f"File: {os.path.basename(video_path)}")
            print(f"Duration: {metadata.get('Composite:Duration', 'N/A')}")
            print(f"Frame Rate: {metadata.get('Composite:VideoFrameRate', 'N/A')}")
            print(f"Codec: {metadata.get('QuickTime:CompressorName', 'N/A')}")
            print(f"Resolution: {metadata.get('Composite:ImageSize', 'N/A')}")
            print(f"Bit Rate: {metadata.get('Composite:AvgBitrate', 'N/A')}")
            
            # Save to a text file in the same directory as the video
            output_path = os.path.join(os.path.dirname(video_path), "video_metadata_output.txt")
            with open(output_path, "w") as f:
                f.write("=== Video Metadata ===\n")
                f.write(f"File: {os.path.basename(video_path)}\n")
                f.write(f"Duration: {metadata.get('Composite:Duration', 'N/A')}\n")
                f.write(f"Frame Rate: {metadata.get('Composite:VideoFrameRate', 'N/A')}\n")
                f.write(f"Codec: {metadata.get('QuickTime:CompressorName', 'N/A')}\n")
                f.write(f"Resolution: {metadata.get('Composite:ImageSize', 'N/A')}\n")
                f.write(f"Bit Rate: {metadata.get('Composite:AvgBitrate', 'N/A')}\n")
                
                # Write all metadata
                f.write("\n=== All Metadata ===\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
                    
            print(f"\nVideo metadata saved to '{output_path}'")
    except Exception as e:
        print(f"Error extracting video metadata with exiftool: {e}")

if __name__ == "__main__":
    video_path = r"C:\Users\felix\OFM\Reels\Videos\IMG_4434.mp4"  # Update with your video path
    extract_video_metadata(video_path) 