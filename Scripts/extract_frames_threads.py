import subprocess
import os
import shutil
import sys

def extract_frames(video_path, output_dir, frame_rate=3):
    """Extract frames from an MP4 video using FFmpeg."""
    print(f"Processing video: {video_path}")
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' does not exist.")
        return False
    if os.path.exists(output_dir):
        print(f"Clearing existing output folder: {output_dir}")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    cmd = [
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "-i", video_path,
        "-vf", f"fps={frame_rate}",
        "-q:v", "2",
        f"{output_dir}/frame_%04d.jpg"
    ]
    print(f"FFmpeg command: {' '.join(cmd)}")
    try:
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

def process_threads_videos(base_folders):
    for base_folder in base_folders:
        threads_folder = os.path.join(base_folder, 'Threads')
        if not os.path.exists(threads_folder):
            print(f"No Threads folder in: {base_folder}")
            continue
        for post_folder in os.listdir(threads_folder):
            post_path = os.path.join(threads_folder, post_folder)
            if not os.path.isdir(post_path):
                continue
            # Find all video files in this Post folder
            video_files = [f for f in os.listdir(post_path) if f.lower().endswith('.mp4')]
            for video_file in video_files:
                video_path = os.path.join(post_path, video_file)
                video_name = os.path.splitext(video_file)[0]
                output_dir = os.path.join(post_path, video_name)
                print(f"\nExtracting frames from {video_path} to {output_dir}")
                extract_frames(video_path, output_dir, frame_rate=3)

def main():
    base_folders = [
        r"C:\Users\felix\OFM\Reels\Images\Student",
        r"C:\Users\felix\OFM\Reels\Images\Goth",
        r"C:\Users\felix\OFM\Reels\Images\Nature",
        r"C:\Users\felix\OFM\Reels\Images\Normal",
        r"C:\Users\felix\OFM\Reels\Images\Construction",
        r"C:\Users\felix\OFM\Reels\Images\Gamer"
    ]
    process_threads_videos(base_folders)
    print("\nAll files processed.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 