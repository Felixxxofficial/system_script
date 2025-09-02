import os
import requests
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import io
from PIL import Image
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

# Google Drive configuration
GDRIVE_FOLDER_ID = '1U0cwqYTw1Z3Aa9eavoYNI0TLlC52aBqT'  # Use same folder as reels_uploader
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('airtable_avatar_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_google_drive_creds():
    """Get and refresh Google Drive credentials as needed"""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.info("Found existing token")
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Token expired, attempting to refresh")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            print("\n" + "="*80)
            print("🔐 GOOGLE DRIVE AUTHORIZATION REQUIRED")
            print("="*80)
            print("The script needs permission to upload images to Google Drive.")
            print("\n📋 STEPS TO AUTHORIZE:")
            print("1. A browser window will open automatically")
            print("2. Sign in to your Google account")
            print("3. Click 'Allow' to grant Google Drive permissions")
            print("4. Return to this terminal - the script will continue automatically")
            print("\n⏳ Starting authorization process...")
            print("="*80 + "\n")
            
            logger.info("No valid credentials found, starting new authentication flow")
            # You'll need to place your Google Drive credentials file here
            CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), 'felix_gdrive.json')
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8090, access_type='offline', prompt='consent')
            
            print("\n✅ Authorization successful! Continuing with image processing...\n")
            
            try:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Saved new token to {token_path}")
            except Exception as e:
                logger.error(f"Error saving token: {e}")
    
    return creds

def download_image_from_url(url):
    """Download image from Instagram URL and return original quality buffer"""
    try:
        # Add https:// scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logger.info(f"Downloading image from: {url}")
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Try to preserve original format first
        try:
            # Return original image data without any processing
            buffer = io.BytesIO(response.content)
            buffer.seek(0)
            
            # Verify it's a valid image by trying to open it
            test_img = Image.open(io.BytesIO(response.content))
            test_img.verify()
            
            logger.info(f"Image downloaded successfully - Original format preserved, size: {len(response.content)} bytes")
            return buffer
            
        except Exception as format_error:
            logger.warning(f"Could not preserve original format ({format_error}), converting to high-quality JPEG")
            
            # Fallback: Convert to PIL Image only if original format fails
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary (for transparency)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background
            
            # Create buffer with MAXIMUM quality (100)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=100, optimize=False)
            buffer.seek(0)
            
            logger.info("Image converted to maximum quality JPEG")
            return buffer
        
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None

def upload_to_gdrive(image_buffer, filename):
    """Upload image to Google Drive with public permissions"""
    try:
        logger.info(f"Uploading to Google Drive: {filename}")
        
        # Get fresh credentials
        creds = get_google_drive_creds()
        
        # Create Drive API service
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare the file metadata
        file_metadata = {
            'name': filename,
            'parents': [GDRIVE_FOLDER_ID]
        }
        
        # Create media upload object
        media = MediaIoBaseUpload(
            image_buffer,
            mimetype='image/jpeg',
            resumable=True
        )
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # Make the file publicly viewable
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file.get('id'),
            body=permission
        ).execute()
        
        # Get the direct download link
        file_data = service.files().get(
            fileId=file.get('id'),
            fields='webContentLink'
        ).execute()
        
        web_content_link = file_data.get('webContentLink')
        
        logger.info(f"Successfully uploaded to Google Drive: {web_content_link}")
        return web_content_link
        
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {str(e)}")
        return None

def get_airtable_records():
    """Fetch all records from Airtable"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_records.extend(data.get('records', []))
            
            offset = data.get('offset')
            if not offset:
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Airtable records: {e}")
            break
    
    logger.info(f"Retrieved {len(all_records)} records from Airtable")
    return all_records

def update_record_with_attachment(record_id, gdrive_url, image_field_name='image'):
    """Update Airtable record with Google Drive attachment URL"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Create attachment data with only URL (following reels_uploader format)
    attachment_data = {
        'fields': {
            image_field_name: [
                {
                    'url': gdrive_url
                }
            ]
        }
    }
    
    logger.info(f"Updating record {record_id} with attachment data: {json.dumps(attachment_data, indent=2)}")
    
    try:
        response = requests.patch(url, headers=headers, json=attachment_data)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated record {record_id}")
            return True
        else:
            logger.error(f"Failed to update record {record_id}. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating record {record_id}: {e}")
        return False

def process_records():
    """Main function to process all records"""
    logger.info("Starting avatar conversion process")
    
    # Get all records from Airtable
    records = get_airtable_records()
    
    if not records:
        logger.error("No records found or error fetching records")
        return
    
    processed_count = 0
    error_count = 0
    
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        
        # Get avatar URL from the 'avatar' field
        avatar_url = fields.get('avatar')
        
        # Skip if no avatar URL or if image field already has content
        if not avatar_url:
            logger.info(f"Skipping record {record_id}: No avatar URL")
            continue
            
        if fields.get('image'):
            logger.info(f"Skipping record {record_id}: Image field already populated")
            continue
        
        logger.info(f"Processing record {record_id} with avatar URL: {avatar_url}")
        
        try:
            # Step 1: Download image from Instagram URL
            image_buffer = download_image_from_url(avatar_url)
            if not image_buffer:
                logger.error(f"Failed to download image for record {record_id}")
                error_count += 1
                continue
            
            # Step 2: Upload to Google Drive
            filename = f"avatar_{record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            gdrive_url = upload_to_gdrive(image_buffer, filename)
            
            if not gdrive_url:
                logger.error(f"Failed to upload to Google Drive for record {record_id}")
                error_count += 1
                continue
            
            # Step 3: Update Airtable record with Google Drive URL
            if update_record_with_attachment(record_id, gdrive_url):
                processed_count += 1
                logger.info(f"Successfully processed record {record_id}")
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing record {record_id}: {str(e)}")
            error_count += 1
    
    logger.info(f"Processing complete. Successfully processed: {processed_count}, Errors: {error_count}")

def main():
    """Main entry point"""
    if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME]):
        logger.error("Missing required environment variables. Please check your .env file.")
        return
    
    # Check if Google Drive credentials file exists
    credentials_path = os.path.join(os.path.dirname(__file__), 'felix_gdrive.json')
    if not os.path.exists(credentials_path):
        logger.error(f"Google Drive credentials file not found: {credentials_path}")
        logger.error("Please place your Google Drive API credentials file as 'felix_gdrive.json' in the script directory")
        return
    
    process_records()

if __name__ == "__main__":
    main()