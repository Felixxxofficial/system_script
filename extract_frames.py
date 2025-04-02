import subprocess
import os
import shutil
import sys

def extract_frames(video_path, output_folder="frames", frame_rate=10):  # Changed default to 10 fps
    """Extract frames from an MP4 video using FFmpeg."""
    print(f"Processing video: {video_path}")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' does not exist.")
        return False

    # Create output folder with video name
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_folder = f"frames-{video_name}"
    output_dir = os.path.join(os.path.dirname(video_path), output_folder)
    print(f"Output directory: {output_dir}")
    if os.path.exists(output_dir):
        print("Clearing existing output folder...")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # FFmpeg command with full path to ffmpeg.exe
    cmd = [
        "C:\\ffmpeg\\bin\\ffmpeg.exe",  # Hardcoded full path
        "-i", video_path,
        "-vf", f"fps={frame_rate}",  # Frame rate (frames per second)
        "-q:v", "2",  # Quality
        f"{output_dir}/frame_%04d.jpg"
    ]
    print(f"FFmpeg command: {' '.join(cmd)}")

    try:
        # Run FFmpeg and capture output
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg output:")
        print(result.stdout)
        print(f"Frames extracted to '{output_dir}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error (exit code {e.returncode}):")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("Error: FFmpeg executable not found at C:\\ffmpeg\\bin\\ffmpeg.exe.")
        return False

def main():
    print("Script started.")
    
    # Define the directory containing videos
    video_dir = r"C:\Users\felix\OFM\Reels\Frame"
    
    # Get all MP4 files in the directory
    try:
        video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    except FileNotFoundError:
        print(f"Error: Directory '{video_dir}' not found.")
        input("Press Enter to exit...")
        return
    
    if not video_files:
        print(f"No MP4 files found in '{video_dir}'.")
        input("Press Enter to exit...")
        return
    
    print(f"Found {len(video_files)} MP4 files to process:")
    for video_file in video_files:
        print(f"- {video_file}")
    
    # Process each video
    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        print(f"\nProcessing: {video_file}")
        
        # Extract frames with adjustable frame rate
        success = extract_frames(video_path, frame_rate=3)  # Adjust frame_rate here
        if success:
            print(f"Extraction completed successfully for {video_file}!")
        else:
            print(f"Extraction failed for {video_file}. See errors above for details.")
    
    print("\nAll files processed.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()