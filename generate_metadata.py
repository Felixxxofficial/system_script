import exiftool
import os
from datetime import datetime, timedelta, UTC
import random
import uuid

def generate_metadata(image_path):
    # Check if the path is a directory
    if os.path.isdir(image_path):
        # Process all JPG/PNG files in the directory
        for filename in os.listdir(image_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                full_path = os.path.join(image_path, filename)
                _process_single_image(full_path)
        return
    
    # If it's a single file, process it
    _process_single_image(image_path)

def _process_single_image(image_path):
    # Skip files that already have _metadata in their name
    if '_metadata' in image_path.lower():
        print(f"Skipping already processed file: {image_path}")
        return

    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return

    # Create new filename with _metadata
    base, ext = os.path.splitext(image_path)
    new_path = f"{base}_metadata{ext}"

    ext = ext.lower()
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

    # iPhone-style filename (IMG_XXXX)
    img_number = random.randint(1, 9999)  # Random 4-digit number
    new_filename = f"IMG_{img_number:04d}{ext}"  # e.g., IMG_1234.jpg

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
        "File:Directory": os.path.dirname(image_path),
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

    # Apply metadata using exiftool
    try:
        with exiftool.ExifToolHelper() as et:
            # Copy file first to preserve original
            os.rename(image_path, new_path)
            # Apply metadata to the new file
            et.set_tags(new_path, metadata, params=["-overwrite_original"])
            print(f"Metadata successfully applied to {new_path}")
            # Save metadata to a file for review
            metadata_file = os.path.join(os.path.dirname(new_path), "applied_metadata.txt")
            with open(metadata_file, "a") as f:
                f.write(f"=== Applied Metadata to {new_path} ===\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
            print(f"Metadata saved to '{metadata_file}'")
    except Exception as e:
        print(f"Error applying metadata: {e}")

if __name__ == "__main__":
    # Process all images in the specified folder
    folder_path = r"C:\Users\felix\OFM\Reels\Lightroom"
    generate_metadata(folder_path)