import exiftool
import os
from datetime import datetime, timedelta, UTC
import random
import uuid
from moviepy.editor import VideoFileClip

def generate_metadata(video_path):
    if os.path.isdir(video_path):
        for filename in os.listdir(video_path):
            if filename.lower().endswith(('.mov', '.mp4')):
                full_path = os.path.join(video_path, filename)
                _process_single_video(full_path)
        return
    _process_single_video(video_path)

def _process_single_video(video_path):
    if '_metadata' in video_path.lower():
        print(f"Skipping already processed file: {video_path}")
        return

    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' not found.")
        return

    base, ext = os.path.splitext(video_path)
    new_path = f"{base}_metadata{ext}"

    ext = ext.lower()
    if ext not in [".mov", ".mp4"]:
        print(f"Error: Only MOV and MP4 are supported. Got {ext}")
        return
    mime_type = "video/quicktime" if ext == ".mov" else "video/mp4"

    now = datetime.now(UTC)
    time_offset = random.randint(1, 6)
    capture_time = now - timedelta(hours=time_offset)
    capture_time_str = capture_time.strftime("%Y:%m:%d %H:%M:%S")

    la_base_lat, la_base_lon = 34.0522, -118.2437
    gps_lat = la_base_lat + random.uniform(-0.05, 0.05)
    gps_lon = la_base_lon + random.uniform(-0.05, 0.05)
    gps_alt = random.randint(20, 100)

    file_size = os.path.getsize(video_path)
    try:
        with VideoFileClip(video_path) as video:
            duration = video.duration
    except Exception as e:
        print(f"Error extracting duration: {e}. Using fallback duration.")
        duration = random.uniform(10, 30)
    
    frame_rate = round(random.uniform(29.97, 30.00), 6)
    resolution_width, resolution_height = 1080, 1920
    bitrate = random.randint(13000000, 15000000)

    img_number = random.randint(1, 9999)
    new_filename = f"IMG_{img_number:04d}{ext}"

    static_metadata = {
        "File:FileType": ext[1:].upper(),
        "File:FileTypeExtension": ext[1:].upper(),
        "File:MIMEType": mime_type,
        "QuickTime:MajorBrand": "qt  ",
        "QuickTime:MinorVersion": "0.0.0",
        "QuickTime:CompatibleBrands": "['qt  ']",
        "QuickTime:MovieHeaderVersion": 0,
        "QuickTime:TimeScale": 600,
        "QuickTime:PreferredRate": 1,
        "QuickTime:PreferredVolume": 1,
        "QuickTime:PreviewTime": 0,
        "QuickTime:PreviewDuration": 0,
        "QuickTime:PosterTime": 0,
        "QuickTime:SelectionTime": 0,
        "QuickTime:SelectionDuration": 0,
        "QuickTime:CurrentTime": 0,
        "QuickTime:NextTrackID": 7,
        "QuickTime:TrackHeaderVersion": 0,
        "QuickTime:TrackLayer": 0,
        "QuickTime:TrackVolume": 0,
        "QuickTime:ImageWidth": resolution_width,
        "QuickTime:ImageHeight": resolution_height,
        "QuickTime:CleanApertureDimensions": f"{resolution_width} {resolution_height}",
        "QuickTime:ProductionApertureDimensions": f"{resolution_width} {resolution_height}",
        "QuickTime:EncodedPixelsDimensions": f"{resolution_width} {resolution_height}",
        "QuickTime:GraphicsMode": 64,
        "QuickTime:OpColor": "32768 32768 32768",
        "QuickTime:CompressorID": "hvc1",
        "QuickTime:CompressorName": "HEVC",
        "QuickTime:BitDepth": 24,
        "QuickTime:LensModel": "iPhone 13 Pro back triple camera 5.7mm f/1.5",
        "QuickTime:FocalLengthIn35mmFormat": 26,
        "QuickTime:XResolution": 72,
        "QuickTime:YResolution": 72,
        "QuickTime:Make": "Apple",
        "QuickTime:Model": "iPhone 13 Pro",
        "QuickTime:Software": "18.0",
        "QuickTime:AudioFormat": "mp4a",
        "QuickTime:AudioChannels": 2,
        "QuickTime:AudioBitsPerSample": 16,
        "QuickTime:AudioSampleRate": 44100,
        "QuickTime:HandlerClass": "dhlr",
        "QuickTime:HandlerVendorID": "appl",
        "QuickTime:HandlerDescription": "Core Media Data Handler",
    }

    dynamic_metadata = {
        "File:FileName": new_filename,
        "File:Directory": os.path.dirname(video_path),
        "File:FileSize": file_size,
        "File:FileModifyDate": f"{capture_time_str}+00:00",
        "File:FileAccessDate": f"{capture_time_str}+00:00",
        "File:FileCreateDate": f"{capture_time_str}+00:00",
        "QuickTime:CreateDate": capture_time_str,
        "QuickTime:ModifyDate": capture_time_str,
        "QuickTime:TrackCreateDate": capture_time_str,
        "QuickTime:TrackModifyDate": capture_time_str,
        "QuickTime:MediaCreateDate": capture_time_str,
        "QuickTime:MediaModifyDate": capture_time_str,
        "QuickTime:Duration": duration,
        "QuickTime:TrackDuration": duration,
        "QuickTime:MediaDuration": duration,
        "QuickTime:VideoFrameRate": frame_rate,
        "QuickTime:AvgBitrate": bitrate,
        "QuickTime:GPSCoordinates": f"{gps_lat} {gps_lon} {gps_alt}",
        "QuickTime:LocationAccuracyHorizontal": random.uniform(20, 30),
        "QuickTime:CreationDate": f"{capture_time_str}-08:00",
        "Composite:ImageSize": f"{resolution_width} {resolution_height}",
        "Composite:Megapixels": 2.0736,
        "Composite:AvgBitrate": bitrate,
        "Composite:GPSAltitude": gps_alt,
        "Composite:GPSAltitudeRef": 0,
        "Composite:GPSLatitude": gps_lat,
        "Composite:GPSLongitude": gps_lon,
        "Composite:GPSPosition": f"{gps_lat} {gps_lon}",
        "Composite:LensID": "iPhone 13 Pro back triple camera 5.7mm f/1.5",
    }

    metadata = {**static_metadata, **dynamic_metadata}

    try:
        with exiftool.ExifToolHelper() as et:
            os.rename(video_path, new_path)
            # Force overwrite of key fields, including the missing aperture/pixel tags
            et.execute(
                "-XMP:all=",  # Remove all XMP tags
                "-QuickTime:ImageWidth=1080",
                "-QuickTime:ImageHeight=1920",
                "-QuickTime:CleanApertureDimensions=1080 1920",
                "-QuickTime:ProductionApertureDimensions=1080 1920",
                "-QuickTime:EncodedPixelsDimensions=1080 1920",
                "-QuickTime:CompressorID=hvc1",
                "-QuickTime:CompressorName=HEVC",
                "-QuickTime:VideoFrameRate=" + str(frame_rate),
                "-QuickTime:AvgBitrate=" + str(bitrate),
                new_path
            )
            # Apply the full metadata set
            et.set_tags(new_path, metadata, params=["-overwrite_original"])
            print(f"Metadata successfully applied to {new_path}")
            metadata_file = os.path.join(os.path.dirname(new_path), "applied_metadata.txt")
            with open(metadata_file, "a") as f:
                f.write(f"=== Applied Metadata to {new_path} ===\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
            print(f"Metadata saved to '{metadata_file}'")
    except Exception as e:
        print(f"Error applying metadata: {e}")

if __name__ == "__main__":
    folder_path = r"C:\Users\felix\OFM\Reels\Videos"
    generate_metadata(folder_path)