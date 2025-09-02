#!/usr/bin/env python3
"""
Google Sheets to Airtable Image Uploader

This script reads image URLs from Google Sheets (column G) and uploads them
as attachments to Airtable records.

Author: AI Assistant
Date: 2025
"""

import os
import sys
import logging
import requests
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from pathlib import Path

# Google Sheets API imports
try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Airtable API (using requests)
try:
    import requests
except ImportError:
    print("Requests library not installed. Run: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sheets_airtable_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SheetsToAirtableUploader:
    """Main class for handling Google Sheets to Airtable image uploads."""
    
    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the uploader with configuration.
        
        Args:
            config: Dictionary containing API keys and configuration
        """
        self.config = config
        self.sheets_service = None
        self.validate_config()
        
    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required_keys = [
            'google_credentials_file',
            'spreadsheet_id',
            'airtable_api_key',
            'airtable_base_id',
            'airtable_table_name',
            'airtable_record_id'
        ]
        
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
            
        # Validate Google credentials file exists
        if not Path(self.config['google_credentials_file']).exists():
            raise FileNotFoundError(f"Google credentials file not found: {self.config['google_credentials_file']}")
    
    def authenticate_google_sheets(self) -> None:
        """Authenticate with Google Sheets API."""
        try:
            creds = None
            token_file = 'token.json'
            
            # Load existing token if available
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config['google_credentials_file'], self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("Successfully authenticated with Google Sheets API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise
    
    def read_image_url_from_sheets(self, cell_range: str = 'G2') -> Optional[str]:
        """Read image URL from specified Google Sheets cell.
        
        Args:
            cell_range: Cell range to read (default: 'G2')
            
        Returns:
            Image URL string or None if not found
        """
        try:
            if not self.sheets_service:
                self.authenticate_google_sheets()
            
            # Read the specified cell
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.config['spreadsheet_id'],
                range=cell_range
            ).execute()
            
            values = result.get('values', [])
            
            if not values or not values[0]:
                logger.warning(f"No data found in cell {cell_range}")
                return None
            
            url = values[0][0].strip()
            logger.info(f"Retrieved URL from {cell_range}: {url}")
            
            # Validate URL format
            if not self.is_valid_url(url):
                logger.error(f"Invalid URL format: {url}")
                return None
                
            return url
            
        except Exception as e:
            logger.error(f"Failed to read from Google Sheets: {e}")
            return None
    
    def is_valid_url(self, url: str) -> bool:
        """Validate if the provided string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL.
        
        Args:
            url: Image URL to download
            
        Returns:
            Image bytes or None if download fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if response contains image data
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {content_type}")
                return None
            
            logger.info(f"Successfully downloaded image ({len(response.content)} bytes)")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None
    
    def upload_to_airtable(self, image_url: str) -> bool:
        """Upload image URL as attachment to Airtable.
        
        Args:
            image_url: URL of the image to upload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Airtable API endpoint
            base_url = f"https://api.airtable.com/v0/{self.config['airtable_base_id']}"
            table_url = f"{base_url}/{self.config['airtable_table_name']}/{self.config['airtable_record_id']}"
            
            headers = {
                'Authorization': f"Bearer {self.config['airtable_api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare attachment data
            attachment_data = {
                'fields': {
                    self.config.get('airtable_attachment_field', 'Attachments'): [
                        {
                            'url': image_url
                        }
                    ]
                }
            }
            
            # Make PATCH request to update the record
            response = requests.patch(table_url, json=attachment_data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully uploaded attachment to Airtable record {self.config['airtable_record_id']}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload to Airtable: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False
    
    def process_upload(self, cell_range: str = 'G2') -> bool:
        """Main method to process the upload from Google Sheets to Airtable.
        
        Args:
            cell_range: Google Sheets cell range to read from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting upload process...")
            
            # Step 1: Read URL from Google Sheets
            image_url = self.read_image_url_from_sheets(cell_range)
            if not image_url:
                logger.error("Failed to retrieve valid image URL from Google Sheets")
                return False
            
            # Step 2: Validate that the URL is accessible
            image_data = self.download_image(image_url)
            if not image_data:
                logger.error("Failed to download/validate image from URL")
                return False
            
            # Step 3: Upload to Airtable
            success = self.upload_to_airtable(image_url)
            if success:
                logger.info("Upload process completed successfully!")
            else:
                logger.error("Upload process failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error during upload process: {e}")
            return False

def main():
    """Main function to run the uploader."""
    # Configuration - Replace with your actual values
    config = {
        # Google Sheets Configuration
        'google_credentials_file': 'credentials.json',  # Download from Google Cloud Console
        'spreadsheet_id': 'your_spreadsheet_id_here',  # From Google Sheets URL
        
        # Airtable Configuration
        'airtable_api_key': 'your_airtable_api_key_here',  # From Airtable Account settings
        'airtable_base_id': 'your_base_id_here',  # From Airtable API documentation
        'airtable_table_name': 'ImageTable',  # Your table name
        'airtable_record_id': 'rec123456789',  # The record ID to update
        'airtable_attachment_field': 'Attachments'  # The attachment field name
    }
    
    try:
        # Create uploader instance
        uploader = SheetsToAirtableUploader(config)
        
        # Process the upload
        success = uploader.process_upload('G2')
        
        if success:
            print("✅ Image successfully uploaded to Airtable!")
        else:
            print("❌ Upload failed. Check the logs for details.")
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()