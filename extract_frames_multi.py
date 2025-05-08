import subprocess
import os
import shutil
import sys

def extract_frames(video_path, output_dir, frame_rate=3):
    """Extract frames from an MP4 video using FFmpeg."""
    print(f"Processing video: {video_path}")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' does not exist.")
        return False

    # Create a subfolder for this specific video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_output_dir = os.path.join(output_dir, video_name)
    
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

def process_directory(frames_dir):
    """Process all MP4 files in a frames directory and extract frames to subdirectories."""
    print(f"\nProcessing directory: {frames_dir}")
    
    # Check if directory exists
    if not os.path.exists(frames_dir):
        print(f"Error: Frames directory '{frames_dir}' not found.")
        # Create the directory if it doesn't exist
        try:
            os.makedirs(frames_dir)
            print(f"Created directory: {frames_dir}")
        except Exception as e:
            print(f"Failed to create directory: {e}")
            return False
    
    # Get all MP4 files in the directory
    try:
        video_files = [f for f in os.listdir(frames_dir) if f.lower().endswith('.mp4')]
    except FileNotFoundError:
        print(f"Error: Could not access directory '{frames_dir}'.")
        return False
    
    if not video_files:
        print(f"No MP4 files found in '{frames_dir}'.")
        return True
    
    print(f"Found {len(video_files)} MP4 files to process in {frames_dir}:")
    for video_file in video_files:
        print(f"- {video_file}")
    
    # Process each video
    success_count = 0
    for video_file in video_files:
        video_path = os.path.join(frames_dir, video_file)
        print(f"\nProcessing: {video_file}")
        
        # Extract frames
        if extract_frames(video_path, frames_dir, frame_rate=3):
            print(f"Extraction completed successfully for {video_file}!")
            success_count += 1
        else:
            print(f"Extraction failed for {video_file}. See errors above for details.")
    
    print(f"\nProcessed {success_count} out of {len(video_files)} videos in {frames_dir}")
    return True

def main():
    print("Frame Extraction Script Started")
    
    # Define frames directories to process
    frames_directories = [
        r"C:\Users\felix\OFM\Reels\Images\Student\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Goth\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Nature\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Normal\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Construction\Frames",
        r"C:\Users\felix\OFM\Reels\Images\Gamer\Frames"
    ]
    
    # Process each directory
    total_dirs = len(frames_directories)
    processed_dirs = 0
    
    for frames_dir in frames_directories:
        if process_directory(frames_dir):
            processed_dirs += 1
    
    print(f"\nProcessed {processed_dirs} out of {total_dirs} directories")
    print("Frame extraction complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 