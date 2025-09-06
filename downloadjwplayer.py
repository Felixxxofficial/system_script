import m3u8
import requests
import os
import subprocess
import urllib.parse
import argparse

def download_m3u8_to_mp4(m3u8_url, output_file="output.mp4", headers=None):
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Referer": "https://hotleak.vip/"
        }
    
    # Parse query parameters from the M3U8 URL
    parsed_url = urllib.parse.urlparse(m3u8_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    # Clean query parameters to remove list formatting
    query_params = {k: v[0] for k, v in query_params.items()}
    
    # Load the M3U8 playlist
    try:
        response = requests.get(m3u8_url, headers=headers)
        response.raise_for_status()
        playlist = m3u8.load(m3u8_url, headers=headers)
    except Exception as e:
        print(f"Error loading M3U8 playlist: {e}")
        return
    
    # Create a temporary directory for TS segments
    os.makedirs("temp_segments", exist_ok=True)
    
    # Download each segment
    segment_files = []
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{os.path.dirname(parsed_url.path)}/"
    for i, segment in enumerate(playlist.segments):
        segment_url = segment.uri
        if not segment_url.startswith("http"):
            segment_url = base_url + segment_url
        
        # Append query parameters to segment URL
        parsed_segment_url = urllib.parse.urlparse(segment_url)
        segment_query_params = urllib.parse.parse_qs(parsed_segment_url.query)
        # Merge original M3U8 query params with segment-specific ones
        combined_params = {**query_params, **{k: v[0] for k, v in segment_query_params.items()}}
        segment_url_with_params = f"{parsed_segment_url.scheme}://{parsed_segment_url.netloc}{parsed_segment_url.path}?{urllib.parse.urlencode(combined_params)}"
        
        try:
            response = requests.get(segment_url_with_params, headers=headers, stream=True)
            response.raise_for_status()
            segment_file = f"temp_segments/segment_{i}.ts"
            with open(segment_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            segment_files.append(segment_file)
            print(f"Downloaded segment {i+1}/{len(playlist.segments)}")
        except Exception as e:
            print(f"Error downloading segment {i}: {e}")
            print(f"Failed URL: {segment_url_with_params}")
            return
    
    # Create a file list for FFmpeg
    file_list_path = "temp_segments/file_list.txt"
    with open(file_list_path, "w") as f:
        for segment_file in segment_files:
            f.write(f"file '{segment_file}'\n")
    
    # Use FFmpeg to concatenate segments into MP4
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", file_list_path, "-c", "copy", output_file
        ], check=True)
        print(f"Successfully created {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg processing: {e}")
        return
    
    # Clean up temporary files
    try:
        for segment_file in segment_files:
            os.remove(segment_file)
        os.remove(file_list_path)
        os.rmdir("temp_segments")
        print("Cleaned up temporary files")
    except Exception as e:
        print(f"Error cleaning up: {e}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Download and convert M3U8 playlist to MP4")
    parser.add_argument("url", nargs="?", help="M3U8 URL to download")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output file name (default: output.mp4)")
    parser.add_argument("-r", "--referer", default="https://hotleak.vip/", help="Referer header value")
    args = parser.parse_args()
    
    # Use command line argument if provided, otherwise use the default URL
    m3u8_url = args.url
    if not m3u8_url:
        print("Please provide an M3U8 URL as an argument.")
        print("Example: python downloadjwplayer.py https://example.com/video.m3u8")
        exit(1)
    
    # Add custom headers
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Referer": args.referer,
    }
    
    download_m3u8_to_mp4(m3u8_url, args.output, headers=custom_headers)