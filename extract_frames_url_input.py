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

def process_single_video(video_path):
    """Process a single video file and extract frames to a Frames subfolder in the same directory."""
    print(f"\nProcessing video file: {video_path}")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return False
    
    # Get the directory containing the video file
    video_dir = os.path.dirname(video_path)
    
    # Create Frames subfolder within the video directory
    frames_dir = os.path.join(video_dir, "Frames")
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
        print(f"Created frames directory: {frames_dir}")
    
    # Extract frames from the video
    if extract_frames(video_path, frames_dir, frame_rate=3):
        print(f"Extraction completed successfully for {os.path.basename(video_path)}!")
        return True
    else:
        print(f"Extraction failed for {os.path.basename(video_path)}. See errors above for details.")
        return False

def main():
    print("Frame Extraction Script (Interactive Version)")
    print("This script will extract frames from a video file you specify.")
    
    while True:
        # Prompt user for video file path
        print("\nPlease enter the full path to your video file:")
        video_path = input("Video path: ").strip()
        
        # Remove quotes if present (in case user wraps path in quotes)
        video_path = video_path.strip('"').strip("'")
        
        # Check if user wants to exit
        if video_path.lower() in ['exit', 'quit', 'q']:
            print("Exiting...")
            break
        
        # Validate the path
        if not video_path:
            print("Error: Please enter a valid path.")
            continue
        
        if not os.path.exists(video_path):
            print(f"Error: File '{video_path}' does not exist. Please check the path and try again.")
            continue
        
        if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')):
            print("Warning: File doesn't appear to be a common video format. Continuing anyway...")
        
        print(f"\nSelected video: {video_path}")
        
        # Process the video
        if process_single_video(video_path):
            print("\nFrame extraction completed successfully!")
        else:
            print("\nFrame extraction failed.")
        
        # Ask if user wants to process another video
        while True:
            another = input("\nDo you want to process another video? (y/n): ").strip().lower()
            if another in ['y', 'yes']:
                break
            elif another in ['n', 'no']:
                print("Goodbye!")
                return
            else:
                print("Please enter 'y' for yes or 'n' for no.")

if __name__ == "__main__":
    main()