import exiftool
import os
import shutil
from datetime import datetime, timedelta, UTC
import random
import uuid
import re
import time
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    print("Warning: moviepy not installed. Video duration will use fallback values.")
    VideoFileClip = None

def process_folders():
    # Define folders to process for images
    image_folders = [
        r"C:\Users\felix\OFM\Reels\Images\Student\Images",
        r"C:\Users\felix\OFM\Reels\Images\Goth\Images",
        r"C:\Users\felix\OFM\Reels\Images\Nature\Images",
        r"C:\Users\felix\OFM\Reels\Images\Normal\Images",
        r"C:\Users\felix\OFM\Reels\Images\Construction\Images",  # New folder for images
        r"C:\Users\felix\OFM\Reels\Images\Gamer\Images"  # New folder for Gamer images
    ]
    
    # Define folders to process for videos
    video_folders = [
        r"C:\Users\felix\OFM\Reels\Images\Student\Video",
        r"C:\Users\felix\OFM\Reels\Images\Goth\Video",
        r"C:\Users\felix\OFM\Reels\Images\Nature\Video",
        r"C:\Users\felix\OFM\Reels\Images\Normal\Video",
        r"C:\Users\felix\OFM\Reels\Images\Construction\Video",  # New folder for videos
        r"C:\Users\felix\OFM\Reels\Images\Gamer\Video"  # New folder for Gamer videos
    ]
    
    # Process each image folder
    print("=== Processing Image Folders ===")
    for folder in image_folders:
        # Ensure folder exists
        if not os.path.exists(folder):
            print(f"Warning: Folder {folder} does not exist. Creating it.")
            os.makedirs(folder, exist_ok=True)
        
        print(f"Processing folder: {folder}")
        process_image_folder(folder)
        print(f"Completed processing: {folder}\n")
    
    # Process each video folder
    print("\n=== Processing Video Folders ===")
    for folder in video_folders:
        # Ensure folder exists
        if not os.path.exists(folder):
            print(f"Warning: Folder {folder} does not exist. Creating it.")
            os.makedirs(folder, exist_ok=True)
        
        print(f"Processing folder: {folder}")
        process_video_folder(folder)
        print(f"Completed processing: {folder}\n")

def get_existing_img_numbers(folder_path):
    """Get list of existing IMG_XXXX numbers in the folder"""
    existing_numbers = set()
    if os.path.exists(folder_path):
        img_pattern = re.compile(r'IMG_(\d{4})\.(jpg|jpeg|png|mov|mp4)', re.IGNORECASE)
        for filename in os.listdir(folder_path):
            match = img_pattern.match(filename)
            if match:
                existing_numbers.add(int(match.group(1)))
    return existing_numbers

def generate_unique_img_number(existing_numbers):
    """Generate a unique IMG number that doesn't exist in the folder"""
    while True:
        img_number = random.randint(1, 9999)
        if img_number not in existing_numbers:
            return img_number

# Process image folder
def process_image_folder(folder_path):
    # Get existing IMG numbers from the folder
    existing_numbers = get_existing_img_numbers(folder_path)
    
    # Collect all files to process first
    files_to_process = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Skip files that already have IMG_ prefix (already processed)
            if filename.startswith('IMG_'):
                print(f"Skipping already processed file: {filename}")
                continue
            
            files_to_process.append(filename)
    
    if not files_to_process:
        print(f"No image files to process in {folder_path}")
        return
    
    print(f"Found {len(files_to_process)} image files to process in {folder_path}")
    
    # Process each file
    for filename in files_to_process:
        full_path = os.path.join(folder_path, filename)
        process_image(full_path, folder_path, existing_numbers)
        # Update the existing numbers after each file is processed
        existing_numbers = get_existing_img_numbers(folder_path)

# Process video folder
def process_video_folder(folder_path):
    # Get existing IMG numbers from the folder
    existing_numbers = get_existing_img_numbers(folder_path)
    
    # Collect all files to process first
    files_to_process = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.mov', '.mp4')):
            # Skip files that already have IMG_ prefix (already processed)
            if filename.startswith('IMG_'):
                print(f"Skipping already processed file: {filename}")
                continue
            
            files_to_process.append(filename)
    
    if not files_to_process:
        print(f"No video files to process in {folder_path}")
        return
    
    print(f"Found {len(files_to_process)} video files to process in {folder_path}")
    
    # Process each file
    for filename in files_to_process:
        full_path = os.path.join(folder_path, filename)
        process_video(full_path, folder_path, existing_numbers)
        # Update the existing numbers after each file is processed
        existing_numbers = get_existing_img_numbers(folder_path)

def get_dropbox_folder(source_folder):
    """Get the corresponding Dropbox folder name based on the source folder"""
    # Extract the category name from the source folder path
    parts = source_folder.split(os.sep)
    for part in parts:
        if part in ['Student', 'Goth', 'Nature', 'Normal', 'Construction', 'Gamer']:
            return os.path.join(r"C:\Users\felix\Dropbox", part)
    return None

# Process a single image file
def process_image(image_path, destination_folder, existing_numbers):
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        print(f"Error: Only JPG and PNG are supported. Got {ext}")
        return
    mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    # Get current time (UTC) and subtract random hours (1-6 hours ago)
    now = datetime.now(UTC)
    time_offset = random.randint(1, 6)  # Hours ago
    capture_time = now - timedelta(hours=time_offset)
    capture_time_str = capture_time.strftime("%Y:%m:%d %H:%M:%S")
    sub_sec = str(random.randint(100, 999))  # Random sub-second

    # Los Angeles GPS coordinates with slight variation
    la_base_lat = 34.0522  # N
    la_base_lon = -118.2437  # W
    lat_variation = random.uniform(-0.05, 0.05)  # ~5.5km radius
    lon_variation = random.uniform(-0.05, 0.05)
    gps_lat = la_base_lat + lat_variation
    gps_lon = la_base_lon + lon_variation
    gps_alt = random.randint(20, 100)  # Altitude in meters, LA range

    # File size
    file_size = os.path.getsize(image_path)

    # Generate unique iPhone-style filename (IMG_XXXX)
    img_number = generate_unique_img_number(existing_numbers)
    new_filename = f"IMG_{img_number:04d}{ext}"  # e.g., IMG_1234.jpg
    new_path = os.path.join(destination_folder, new_filename)
    
    # Ensure new filename doesn't already exist
    while os.path.exists(new_path):
        print(f"  Warning: Target file already exists: {new_path}")
        img_number = generate_unique_img_number(existing_numbers)
        new_filename = f"IMG_{img_number:04d}{ext}"
        new_path = os.path.join(destination_folder, new_filename)
        print(f"  Generated new unique filename: {new_filename}")

    # Static metadata (iPhone 13 Pro, no rotation)
    static_metadata = {
        "File:FileType": ext[1:].upper(),  # JPG or PNG
        "File:FileTypeExtension": ext[1:].upper(),
        "File:MIMEType": mime_type,
        "File:ImageWidth": 3024,
        "File:ImageHeight": 4032,
        "XMP:XMPToolkit": "XMP Core 6.0.0",
        "EXIF:Make": "Apple",
        "EXIF:Model": "iPhone 13 Pro",
        "EXIF:Orientation": 1,  # No rotation, image stays as-is
        "EXIF:XResolution": 72,
        "EXIF:YResolution": 72,
        "EXIF:ResolutionUnit": 2,
        "EXIF:Software": "18.0",
        "EXIF:HostComputer": "iPhone 13 Pro",
        "EXIF:ExifVersion": "0232",
        "EXIF:ColorSpace": 65535,
        "EXIF:ExifImageWidth": 3024,
        "EXIF:ExifImageHeight": 4032,
        "EXIF:SensingMethod": 2,
        "EXIF:SceneType": 1,
        "EXIF:LensInfo": "1.570000052 9 1.5 2.8",
        "EXIF:LensMake": "Apple",
        "EXIF:LensModel": "iPhone 13 Pro back triple camera 5.7mm f/1.5",
        "EXIF:FocalLength": 5.7,
        "EXIF:FNumber": 1.5,
        "EXIF:FocalLengthIn35mmFormat": 26,
        "MakerNotes:MakerNoteVersion": 15,
        "MakerNotes:RunTimeScale": 1000000000,
        "MakerNotes:RunTimeEpoch": 0,
        "ICC_Profile:ProfileDescription": "Display P3",
        "ICC_Profile:ProfileCopyright": "Copyright Apple Inc., 2022",
    }

    # Dynamic metadata
    exposure_time = random.choice([0.00025, 0.001, 0.002, 0.01])  # Define first
    dynamic_metadata = {
        "File:FileName": new_filename,  # iPhone-style filename
        "File:Directory": destination_folder,
        "File:FileSize": file_size,
        "File:FileModifyDate": f"{capture_time_str}+00:00",
        "File:FileAccessDate": f"{capture_time_str}+00:00",
        "File:FileCreateDate": f"{capture_time_str}+00:00",
        "XMP:CreateDate": capture_time_str,
        "XMP:CreatorTool": "18.0",
        "XMP:ModifyDate": capture_time_str,
        "XMP:DateCreated": capture_time_str,
        "EXIF:ModifyDate": capture_time_str,
        "EXIF:ExposureTime": exposure_time,  # 1/4000s to 1/100s
        "EXIF:ExposureProgram": 2,
        "EXIF:ISO": random.randint(32, 200),  # Daytime range
        "EXIF:DateTimeOriginal": capture_time_str,
        "EXIF:CreateDate": capture_time_str,
        "EXIF:OffsetTime": "-08:00",  # PST for LA
        "EXIF:OffsetTimeOriginal": "-08:00",
        "EXIF:OffsetTimeDigitized": "-08:00",
        "EXIF:ShutterSpeedValue": "{:.6f}".format(exposure_time),
        "EXIF:ApertureValue": 1.5,
        "EXIF:BrightnessValue": random.uniform(6.0, 10.0),  # Daytime
        "EXIF:ExposureCompensation": 0,
        "EXIF:MeteringMode": 5,
        "EXIF:Flash": 16,
        "EXIF:SubSecTimeOriginal": sub_sec,
        "EXIF:SubSecTimeDigitized": sub_sec,
        "EXIF:GPSLatitudeRef": "N",
        "EXIF:GPSLatitude": abs(gps_lat),
        "EXIF:GPSLongitudeRef": "W",
        "EXIF:GPSLongitude": abs(gps_lon),
        "EXIF:GPSAltitudeRef": 0,
        "EXIF:GPSAltitude": gps_alt,
        "EXIF:GPSTimeStamp": capture_time.strftime("%H:%M:%S"),  # UTC time
        "EXIF:GPSDateStamp": capture_time.strftime("%Y:%m:%d"),
        "EXIF:GPSHPositioningError": random.randint(5, 10),
        "MakerNotes:RunTimeValue": random.randint(100000000000000, 500000000000000),
        "MakerNotes:AEStable": 1,
        "MakerNotes:AETarget": random.randint(200, 220),
        "MakerNotes:AEAverage": random.randint(195, 215),
        "MakerNotes:AFStable": 1,
        "MakerNotes:AccelerationVector": f"-0.95 {random.uniform(0.05, 0.15)} {random.uniform(-0.4, -0.2)}",  # Still indicates portrait tilt
        "MakerNotes:FocusDistanceRange": f"{random.uniform(0.5, 3.0):.2f} {random.uniform(0.1, 0.6):.2f}",
        "MakerNotes:ContentIdentifier": str(uuid.uuid4()).upper(),
        "MakerNotes:PhotoIdentifier": str(uuid.uuid4()).upper(),
        "MakerNotes:ColorTemperature": random.randint(4500, 6000),
        "MakerNotes:FocusPosition": random.randint(30, 70),
        "MakerNotes:HDRGain": random.uniform(0.0, 0.3),
        "MakerNotes:SignalToNoiseRatio": random.uniform(35, 40),
    }

    # Combine static and dynamic metadata
    metadata = {**static_metadata, **dynamic_metadata}

    try:
        print(f"Processing image: {os.path.basename(image_path)} → {new_filename}")
        
        # Copy directly to the new filename first
        print(f"  Copying to new file: {new_path}")
        shutil.copy2(image_path, new_path)
        
        # Apply metadata to the new file
        print(f"  Applying metadata")
        with exiftool.ExifToolHelper() as et:
            et.set_tags(new_path, metadata, params=["-overwrite_original"])
        
        # Remove the original file only after successful processing
        print(f"  Removing original: {image_path}")
        os.remove(image_path)
        
        print(f"Successfully processed: {new_path}")
    except Exception as e:
        print(f"Error processing image {os.path.basename(image_path)}: {e}")
        # Cleanup if there was an error
        if os.path.exists(new_path):
            try:
                os.remove(new_path)
                print(f"  Cleaned up new file due to error: {new_path}")
            except Exception as cleanup_err:
                print(f"  Error cleaning up file: {cleanup_err}")

# Process a single video file
def process_video(video_path, destination_folder, existing_numbers):
    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' not found.")
        return

    ext = os.path.splitext(video_path)[1].lower()
    if ext not in [".mov", ".mp4"]:
        print(f"Error: Only MOV and MP4 are supported. Got {ext}")
        return
    mime_type = "video/quicktime" if ext == ".mov" else "video/mp4"

    # Skip if already processed
    if os.path.basename(video_path).startswith('IMG_'):
        print(f"Skipping already processed file: {video_path}")
        return

    # Get current time (UTC) and subtract random hours (1-6 hours ago)
    now = datetime.now(UTC)
    time_offset = random.randint(1, 6)
    capture_time = now - timedelta(hours=time_offset)
    capture_time_str = capture_time.strftime("%Y:%m:%d %H:%M:%S")

    # Los Angeles GPS coordinates with slight variation
    la_base_lat, la_base_lon = 34.0522, -118.2437
    gps_lat = la_base_lat + random.uniform(-0.05, 0.05)
    gps_lon = la_base_lon + random.uniform(-0.05, 0.05)
    gps_alt = random.randint(20, 100)

    # File size
    file_size = os.path.getsize(video_path)
    
    # Try to get video duration
    try:
        if VideoFileClip:
            with VideoFileClip(video_path) as video:
                duration = video.duration
        else:
            raise ImportError("MoviePy not available")
    except Exception as e:
        print(f"  Warning: Error extracting duration: {e}. Using fallback duration.")
        duration = random.uniform(10, 30)
    
    frame_rate = round(random.uniform(29.97, 30.00), 6)
    resolution_width, resolution_height = 1080, 1920
    bitrate = random.randint(13000000, 15000000)

    # Generate unique iPhone-style filename (IMG_XXXX)
    img_number = generate_unique_img_number(existing_numbers)
    new_filename = f"IMG_{img_number:04d}{ext}"  # e.g., IMG_1234.mp4
    new_path = os.path.join(destination_folder, new_filename)
    
    # Ensure new filename doesn't already exist
    while os.path.exists(new_path):
        print(f"  Warning: Target file already exists: {new_path}")
        img_number = generate_unique_img_number(existing_numbers)
        new_filename = f"IMG_{img_number:04d}{ext}"
        new_path = os.path.join(destination_folder, new_filename)
        print(f"  Generated new unique filename: {new_filename}")

    # Static metadata for video
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

    # Dynamic metadata for video
    dynamic_metadata = {
        "File:FileName": new_filename,
        "File:Directory": destination_folder,
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

    # Combine static and dynamic metadata
    metadata = {**static_metadata, **dynamic_metadata}

    try:
        print(f"Processing video: {os.path.basename(video_path)} → {new_filename}")
        
        # Copy directly to the new filename first
        print(f"  Copying to new file: {new_path}")
        shutil.copy2(video_path, new_path)
        
        # Apply metadata to the new file
        print(f"  Applying metadata")
        with exiftool.ExifToolHelper() as et:
            # Force overwrite of key fields
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
        
        # Remove the original file only after successful processing
        print(f"  Removing original: {video_path}")
        os.remove(video_path)
        
        print(f"Successfully processed: {new_path}")
        
        # Copy to Dropbox folder
        dropbox_folder = get_dropbox_folder(destination_folder)
        if dropbox_folder:
            try:
                # Create Dropbox folder if it doesn't exist
                os.makedirs(dropbox_folder, exist_ok=True)
                
                # Copy the renamed video to Dropbox
                dropbox_path = os.path.join(dropbox_folder, new_filename)
                print(f"  Copying to Dropbox: {dropbox_path}")
                shutil.copy2(new_path, dropbox_path)
                print(f"  Successfully copied to Dropbox: {dropbox_path}")
            except Exception as e:
                print(f"  Error copying to Dropbox: {e}")
    except Exception as e:
        print(f"Error processing video {os.path.basename(video_path)}: {e}")
        # Cleanup if there was an error
        if os.path.exists(new_path):
            try:
                os.remove(new_path)
                print(f"  Cleaned up new file due to error: {new_path}")
            except Exception as cleanup_err:
                print(f"  Error cleaning up file: {cleanup_err}")

if __name__ == "__main__":
    process_folders()