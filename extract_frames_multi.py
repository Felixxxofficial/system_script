import subprocess
import os
import shutil
import sys
from datetime import date  # Import the date module

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

def process_directory(video_dir, frames_dir):
    """Process all MP4 files in a video directory and extract frames to the frames directory."""
    print(f"\nProcessing video directory: {video_dir}")
    
    # Check if video directory exists
    if not os.path.exists(video_dir):
        print(f"Error: Video directory '{video_dir}' not found.")
        return False
    
    # Get all MP4 files in the video directory
    try:
        video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    except FileNotFoundError:
        print(f"Error: Could not access directory '{video_dir}'.")
        return False
    
    if not video_files:
        print(f"No MP4 files found in '{video_dir}'.")
        return True
    
    # Find the most recent video based on creation time
    most_recent_video = max(video_files, key=lambda f: os.path.getmtime(os.path.join(video_dir, f)))
    print(f"Most recent video: {most_recent_video}")
    
    # Process the most recent video
    video_path = os.path.join(video_dir, most_recent_video)
    print(f"\nProcessing: {most_recent_video}")
    
    # Extract frames to the frames directory
    if extract_frames(video_path, frames_dir, frame_rate=3):
        print(f"Extraction completed successfully for {most_recent_video}!")
        return True
    else:
        print(f"Extraction failed for {most_recent_video}. See errors above for details.")
        return False

def main():
    print("Frame Extraction Script Started")
    
    # Define video and frames directories to process
    video_directories = [
        r"C:\Users\felix\OFM\Reels\Images\Student\Video",
        r"C:\Users\felix\OFM\Reels\Images\Goth\Video",
        r"C:\Users\felix\OFM\Reels\Images\Nature\Video",
        r"C:\Users\felix\OFM\Reels\Images\Normal\Video",
        r"C:\Users\felix\OFM\Reels\Images\Construction\Video",
        r"C:\Users\felix\OFM\Reels\Images\Gamer\Video"
    ]
    
    frames_directories = [
        r"C:\Users\felix\OFM\Reels\Images\Student\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Goth\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Nature\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Normal\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Construction\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Gamer\Frames"
    ]
    
    # Process each directory
    total_dirs = len(video_directories)
    processed_dirs = 0
    
    for video_dir, frames_dir in zip(video_directories, frames_directories):
        if process_directory(video_dir, frames_dir):
            processed_dirs += 1
    
    print(f"\nProcessed {processed_dirs} out of {total_dirs} directories")
    print("Frame extraction complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 