#!/usr/bin/env python3
"""
CSV to Airtable Instagram Avatar Uploader

This script reads Instagram avatar URLs from a CSV file and uploads them
as attachments to Airtable records.

Author: AI Assistant
Date: 2025
"""

import csv
import logging
import requests
import sys
from typing import List, Dict, Optional
from urllib.parse import urlparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_airtable_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CSVToAirtableUploader:
    """Main class for handling CSV to Airtable image uploads."""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the uploader with configuration.
        
        Args:
            config: Dictionary containing API keys and configuration
        """
        self.config = config
        self.validate_config()
        
    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required_keys = [
            'csv_file_path',
            'airtable_api_key',
            'airtable_base_id',
            'airtable_table_name'
        ]
        
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
            
        # Validate CSV file exists
        if not Path(self.config['csv_file_path']).exists():
            raise FileNotFoundError(f"CSV file not found: {self.config['csv_file_path']}")
    
    def read_csv_data(self) -> List[Dict[str, str]]:
        """Read data from CSV file.
        
        Returns:
            List of dictionaries containing row data
        """
        try:
            data = []
            with open(self.config['csv_file_path'], 'r', encoding='utf-8', newline='') as csvfile:
                # Try to detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
                    if row:
                        row['_row_number'] = row_num
                        data.append(row)
                        
            logger.info(f"Successfully read {len(data)} rows from CSV file")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            raise
    
    def is_valid_instagram_url(self, url: str) -> bool:
        """Validate if the URL is a valid Instagram CDN URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid Instagram URL, False otherwise
        """
        try:
            if not url or not isinstance(url, str):
                return False
                
            url = url.strip()
            if not url:
                return False
                
            # Check if it's a valid URL
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
            
            # Check if it's an Instagram CDN URL
            instagram_domains = [
                'instagram.', 'fbcdn.net', 'cdninstagram.com'
            ]
            
            domain_check = any(domain in result.netloc.lower() for domain in instagram_domains)
            
            # Check if it looks like an image URL
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            has_image_extension = any(ext in url.lower() for ext in image_extensions)
            
            return domain_check and has_image_extension
            
        except Exception:
            return False
    
    def test_url_accessibility(self, url: str) -> bool:
        """Test if the Instagram URL is accessible.
        
        Args:
            url: URL to test
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Use HEAD request to check if URL is accessible without downloading
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if content_type.startswith('image/'):
                    logger.info(f"URL is accessible and returns image content: {url[:100]}...")
                    return True
                else:
                    logger.warning(f"URL accessible but not an image: {content_type}")
                    return False
            else:
                logger.warning(f"URL returned status code {response.status_code}: {url[:100]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"URL accessibility test failed: {e}")
            return False
    
    def upload_to_airtable(self, record_data: Dict[str, str]) -> bool:
        """Upload Instagram avatar URL as attachment to Airtable.
        
        Args:
            record_data: Dictionary containing record data including avatar URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the avatar URL from the specified column
            avatar_column = self.config.get('avatar_url_column', 'G')
            avatar_url = record_data.get(avatar_column, '').strip()
            
            if not avatar_url:
                logger.warning(f"No avatar URL found in column {avatar_column} for row {record_data.get('_row_number')}")
                return False
            
            # Validate Instagram URL
            if not self.is_valid_instagram_url(avatar_url):
                logger.error(f"Invalid Instagram URL: {avatar_url[:100]}...")
                return False
            
            # Test URL accessibility (optional, can be disabled for speed)
            if self.config.get('test_url_accessibility', True):
                if not self.test_url_accessibility(avatar_url):
                    logger.error(f"Instagram URL is not accessible: {avatar_url[:100]}...")
                    return False
            
            # Determine record ID or create new record
            record_id = record_data.get('record_id')
            
            if record_id:
                # Update existing record
                return self._update_airtable_record(record_id, avatar_url)
            else:
                # Create new record
                return self._create_airtable_record(record_data, avatar_url)
                
        except Exception as e:
            logger.error(f"Failed to upload to Airtable: {e}")
            return False
    
    def _update_airtable_record(self, record_id: str, avatar_url: str) -> bool:
        """Update existing Airtable record with avatar attachment.
        
        Args:
            record_id: Airtable record ID
            avatar_url: Instagram avatar URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            base_url = f"https://api.airtable.com/v0/{self.config['airtable_base_id']}"
            table_url = f"{base_url}/{self.config['airtable_table_name']}/{record_id}"
            
            headers = {
                'Authorization': f"Bearer {self.config['airtable_api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare attachment data
            attachment_field = self.config.get('airtable_attachment_field', 'Attachments')
            attachment_data = {
                'fields': {
                    attachment_field: [
                        {
                            'url': avatar_url,
                            'filename': f"avatar_{record_id}.jpg"
                        }
                    ]
                }
            }
            
            # Make PATCH request to update the record
            response = requests.patch(table_url, json=attachment_data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully updated Airtable record {record_id} with avatar")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update Airtable record {record_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False
    
    def _create_airtable_record(self, record_data: Dict[str, str], avatar_url: str) -> bool:
        """Create new Airtable record with avatar attachment.
        
        Args:
            record_data: Dictionary containing record data
            avatar_url: Instagram avatar URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            base_url = f"https://api.airtable.com/v0/{self.config['airtable_base_id']}"
            table_url = f"{base_url}/{self.config['airtable_table_name']}"
            
            headers = {
                'Authorization': f"Bearer {self.config['airtable_api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare record data
            attachment_field = self.config.get('airtable_attachment_field', 'Attachments')
            fields = {
                attachment_field: [
                    {
                        'url': avatar_url,
                        'filename': f"avatar_row_{record_data.get('_row_number', 'unknown')}.jpg"
                    }
                ]
            }
            
            # Add other fields from CSV if specified
            field_mapping = self.config.get('field_mapping', {})
            for csv_column, airtable_field in field_mapping.items():
                if csv_column in record_data and record_data[csv_column]:
                    fields[airtable_field] = record_data[csv_column]
            
            record_payload = {
                'fields': fields
            }
            
            # Make POST request to create the record
            response = requests.post(table_url, json=record_payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            new_record_id = result.get('id')
            
            logger.info(f"Successfully created Airtable record {new_record_id} with avatar")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Airtable record: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False
    
    def process_csv_upload(self) -> Dict[str, int]:
        """Main method to process CSV upload to Airtable.
        
        Returns:
            Dictionary with success/failure counts
        """
        try:
            logger.info("Starting CSV to Airtable upload process...")
            
            # Read CSV data
            csv_data = self.read_csv_data()
            
            if not csv_data:
                logger.error("No data found in CSV file")
                return {'success': 0, 'failed': 0, 'total': 0}
            
            # Process each row
            success_count = 0
            failed_count = 0
            
            for row_data in csv_data:
                try:
                    if self.upload_to_airtable(row_data):
                        success_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing row {row_data.get('_row_number')}: {e}")
                    failed_count += 1
            
            total_count = len(csv_data)
            
            logger.info(f"Upload process completed: {success_count}/{total_count} successful")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during upload process: {e}")
            return {'success': 0, 'failed': 0, 'total': 0}

def main():
    """Main function to run the uploader."""
    # Configuration - Replace with your actual values
    config = {
        # CSV Configuration
        'csv_file_path': 'instagram_avatars.csv',  # Path to your CSV file
        'avatar_url_column': 'G',  # Column containing Instagram avatar URLs
        
        # Airtable Configuration
        'airtable_api_key': 'your_airtable_api_key_here',  # From Airtable Account settings
        'airtable_base_id': 'your_base_id_here',  # From Airtable API documentation
        'airtable_table_name': 'ImageTable',  # Your table name
        'airtable_attachment_field': 'Attachments',  # The attachment field name
        
        # Optional: Field mapping from CSV columns to Airtable fields
        'field_mapping': {
            'A': 'Name',  # Map CSV column A to Airtable field 'Name'
            'B': 'Username',  # Map CSV column B to Airtable field 'Username'
            # Add more mappings as needed
        },
        
        # Optional: Test URL accessibility (set to False for faster processing)
        'test_url_accessibility': True
    }
    
    try:
        # Create uploader instance
        uploader = CSVToAirtableUploader(config)
        
        # Process the upload
        results = uploader.process_csv_upload()
        
        print(f"\n📊 Upload Results:")
        print(f"✅ Successful: {results['success']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📝 Total: {results['total']}")
        
        if results['success'] > 0:
            print(f"\n🎉 {results['success']} Instagram avatars successfully uploaded to Airtable!")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} uploads failed. Check the logs for details.")
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()