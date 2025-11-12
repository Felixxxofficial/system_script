import subprocess
import os
import shutil
import sys
from datetime import date

def extract_frames(video_path, output_dir, frame_rate=3):
    """Extract frames from an MP4 video using FFmpeg."""
    print(f"Processing video: {video_path}")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' does not exist.")
        return False

    # Create a subfolder for this specific video with today's date and video name
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    today_date = date.today().strftime("%Y-%m-%d")
    video_output_dir = os.path.join(output_dir, f"{today_date}_{video_name}")
    
    # Clear existing output folder if it exists
    if os.path.exists(video_output_dir):
        print(f"Clearing existing output folder: {video_output_dir}")
        shutil.rmtree(video_output_dir)
    
    os.makedirs(video_output_dir)
    print(f"Created output directory: {video_output_dir}")

    # FFmpeg command with full path to ffmpeg.exe
    cmd = [
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "-i", video_path,
        "-vf", f"fps={frame_rate}",  # Frame rate (frames per second)
        "-q:v", "2",  # Quality
        f"{video_output_dir}\\frame_%04d.jpg"
    ]
    print(f"FFmpeg command: {' '.join(cmd)}")

    try:
        # Run FFmpeg and capture output
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg command executed successfully.")
        print(f"Frames extracted to '{video_output_dir}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error (exit code {e.returncode}):")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("Error: FFmpeg executable not found at C:\\ffmpeg\\bin\\ffmpeg.exe.")
        return False

def process_all_videos_in_directory(video_dir):
    """Process all MP4 files in a video directory and extract frames to a Frames subfolder."""
    print(f"\nProcessing video directory: {video_dir}")
    
    # Check if video directory exists
    if not os.path.exists(video_dir):
        print(f"Error: Video directory '{video_dir}' not found.")
        return False
    
    # Create Frames subfolder within the video directory
    frames_dir = os.path.join(video_dir, "Frames")
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
        print(f"Created frames directory: {frames_dir}")
    
    # Get all MP4 files in the video directory
    try:
        video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    except FileNotFoundError:
        print(f"Error: Could not access directory '{video_dir}'.")
        return False
    
    if not video_files:
        print(f"No MP4 files found in '{video_dir}'.")
        return True
    
    print(f"Found {len(video_files)} video file(s): {', '.join(video_files)}")
    
    # Process all videos in the directory
    successful_extractions = 0
    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        print(f"\nProcessing: {video_file}")
        
        # Extract frames to the frames directory
        if extract_frames(video_path, frames_dir, frame_rate=3):
            print(f"Extraction completed successfully for {video_file}!")
            successful_extractions += 1
        else:
            print(f"Extraction failed for {video_file}. See errors above for details.")
    
    print(f"\nProcessed {successful_extractions} out of {len(video_files)} videos successfully.")
    return successful_extractions > 0

def main():
    print("Frame Extraction Script (Command Line Version)")
    print("Usage: python extract_frames_cmdline.py <video_folder_path>")
    
    # Check if video folder path is provided as command line argument
    if len(sys.argv) != 2:
        print("\nError: Please provide the video folder path as an argument.")
        print("Example: python extract_frames_cmdline.py \"C:\\path\\to\\video\\folder\"")
        input("Press Enter to exit...")
        return
    
    video_folder = sys.argv[1]
    
    # Remove quotes if present (in case user wraps path in quotes)
    video_folder = video_folder.strip('"').strip("'")
    
    print(f"\nVideo folder: {video_folder}")
    
    # Process the directory
    if process_all_videos_in_directory(video_folder):
        print("\nFrame extraction completed successfully!")
    else:
        print("\nFrame extraction failed or no videos were processed.")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()