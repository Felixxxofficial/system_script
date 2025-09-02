#!/usr/bin/env python3
"""
Update Existing Airtable Records with Instagram Avatar Attachments

This script reads Instagram avatar URLs from your CSV file and updates
existing Airtable records by adding the avatars as attachments to the 'image' field.

Author: AI Assistant
Date: 2025
"""

import csv
import logging
import requests
import sys
import time
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('airtable_avatar_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AirtableAvatarUpdater:
    """Update existing Airtable records with Instagram avatar attachments."""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the updater with configuration.
        
        Args:
            config: Dictionary containing API keys and configuration
        """
        self.config = config
        self.validate_config()
        self.rate_limit_delay = config.get('rate_limit_delay', 0.2)  # 200ms between requests
        
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
            List of dictionaries containing row data with avatar URLs
        """
        try:
            data = []
            with open(self.config['csv_file_path'], 'r', encoding='utf-8', newline='') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip header row
                header = next(reader)
                logger.info(f"CSV Header: {header}")
                
                for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
                    if len(row) >= 7:  # Ensure we have at least 7 columns
                        record_data = {
                            'row_number': row_num,
                            'id': row[0].strip() if row[0] else '',
                            'login': row[1].strip() if row[1] else '',
                            'name': row[4].strip() if len(row) > 4 and row[4] else '',
                            'avatar_url': row[6].strip() if len(row) > 6 and row[6] else '',  # Column 7 (index 6)
                            'link': row[9].strip() if len(row) > 9 and row[9] else ''  # Instagram link
                        }
                        
                        # Only include rows with valid avatar URLs
                        if record_data['avatar_url'] and self.is_valid_instagram_url(record_data['avatar_url']):
                            data.append(record_data)
                        else:
                            logger.warning(f"Row {row_num}: Invalid or missing avatar URL")
                            
            logger.info(f"Successfully read {len(data)} valid records from CSV file")
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
                'instagram.', 'fbcdn.net', 'cdninstagram.com', 'scontent-'
            ]
            
            domain_check = any(domain in result.netloc.lower() for domain in instagram_domains)
            
            # Check if it looks like an image URL (anywhere in the URL, not just at the end)
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            has_image_extension = any(ext in url.lower() for ext in image_extensions)
            
            # Additional check for Instagram-specific patterns
            instagram_patterns = [
                't51.2885-19',  # Instagram profile pic pattern
                'profile_pic',   # Profile picture indicator
                'ig_cache_key'   # Instagram cache key
            ]
            has_instagram_pattern = any(pattern in url.lower() for pattern in instagram_patterns)
            
            return domain_check and (has_image_extension or has_instagram_pattern)
            
        except Exception:
            return False
    
    def get_all_airtable_records(self) -> Dict[str, str]:
        """Get all records from Airtable to match with CSV data.
        
        Returns:
            Dictionary mapping record IDs to Airtable record IDs
        """
        try:
            base_url = f"https://api.airtable.com/v0/{self.config['airtable_base_id']}"
            table_url = f"{base_url}/{self.config['airtable_table_name']}"
            
            headers = {
                'Authorization': f"Bearer {self.config['airtable_api_key']}"
            }
            
            all_records = {}
            offset = None
            
            while True:
                params = {'pageSize': 100}
                if offset:
                    params['offset'] = offset
                
                response = requests.get(table_url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                records = data.get('records', [])
                
                for record in records:
                    record_id = record['id']
                    fields = record.get('fields', {})
                    
                    # Try to match by 'id' field first, then by 'login' field
                    csv_id = fields.get('id', fields.get('login', ''))
                    if csv_id:
                        all_records[str(csv_id)] = record_id
                
                offset = data.get('offset')
                if not offset:
                    break
                    
                time.sleep(self.rate_limit_delay)  # Rate limiting
            
            logger.info(f"Retrieved {len(all_records)} records from Airtable")
            return all_records
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve Airtable records: {e}")
            raise
    
    def update_record_with_avatar(self, airtable_record_id: str, avatar_url: str, record_info: Dict[str, str]) -> bool:
        """Update a single Airtable record with avatar attachment.
        
        Args:
            airtable_record_id: Airtable record ID
            avatar_url: Instagram avatar URL
            record_info: Additional record information for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            base_url = f"https://api.airtable.com/v0/{self.config['airtable_base_id']}"
            record_url = f"{base_url}/{self.config['airtable_table_name']}/{airtable_record_id}"
            
            headers = {
                'Authorization': f"Bearer {self.config['airtable_api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare attachment data for the 'image' field
            image_field = self.config.get('image_field_name', 'image')
            
            # Create filename from login or ID
            filename = f"{record_info.get('login', record_info.get('id', 'avatar'))}_avatar.jpg"
            
            attachment_data = {
                'fields': {
                    image_field: [
                        {
                            'url': avatar_url,
                            'filename': filename
                        }
                    ]
                }
            }
            
            # Make PATCH request to update the record
            response = requests.patch(record_url, json=attachment_data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"✅ Updated record {airtable_record_id} ({record_info.get('login', record_info.get('id'))}) with avatar")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to update record {airtable_record_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False
    
    def process_avatar_updates(self) -> Dict[str, int]:
        """Main method to process avatar updates.
        
        Returns:
            Dictionary with success/failure counts
        """
        try:
            logger.info("Starting avatar update process...")
            
            # Step 1: Read CSV data
            csv_data = self.read_csv_data()
            if not csv_data:
                logger.error("No valid data found in CSV file")
                return {'success': 0, 'failed': 0, 'not_found': 0, 'total': 0}
            
            # Step 2: Get all Airtable records
            logger.info("Retrieving existing Airtable records...")
            airtable_records = self.get_all_airtable_records()
            
            # Step 3: Process each CSV record
            success_count = 0
            failed_count = 0
            not_found_count = 0
            
            for record_data in csv_data:
                try:
                    # Try to find matching Airtable record by ID or login
                    csv_id = record_data['id'] or record_data['login']
                    airtable_record_id = airtable_records.get(csv_id)
                    
                    if not airtable_record_id:
                        logger.warning(f"⚠️  No matching Airtable record found for ID/login: {csv_id}")
                        not_found_count += 1
                        continue
                    
                    # Update the record with avatar
                    if self.update_record_with_avatar(airtable_record_id, record_data['avatar_url'], record_data):
                        success_count += 1
                    else:
                        failed_count += 1
                    
                    # Rate limiting
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Error processing record {record_data.get('id', 'unknown')}: {e}")
                    failed_count += 1
            
            total_count = len(csv_data)
            
            logger.info(f"Avatar update process completed:")
            logger.info(f"✅ Successful updates: {success_count}")
            logger.info(f"❌ Failed updates: {failed_count}")
            logger.info(f"⚠️  Records not found: {not_found_count}")
            logger.info(f"📝 Total processed: {total_count}")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'not_found': not_found_count,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during update process: {e}")
            return {'success': 0, 'failed': 0, 'not_found': 0, 'total': 0}

def main():
    """Main function to run the avatar updater."""
    # Configuration - Replace with your actual values
    config = {
        # CSV Configuration
        'csv_file_path': r'c:\Users\felix\Scripts\all girls details - names_with_gender.csv',
        
        # Airtable Configuration
        'airtable_api_key': 'pat2WbDCJllMf4Bry.800cedbedd4fb8e836cb9060a78204bd4e6fe8b4af381383969b8ed36940f9b0',  # Your Airtable API key
        'airtable_base_id': 'appA8UeJKKZXrMYTj',  # Your Airtable base ID
        'airtable_table_name': 'tblrPtxla961Wvw6Y',  # Your table name
        'image_field_name': 'image',  # The field name where you want to add avatars
        
        # Optional: Rate limiting (seconds between requests)
        'rate_limit_delay': 0.2  # 200ms delay to avoid hitting rate limits
    }
    
    try:
        # Create updater instance
        updater = AirtableAvatarUpdater(config)
        
        # Process the updates
        results = updater.process_avatar_updates()
        
        print(f"\n📊 Avatar Update Results:")
        print(f"✅ Successful updates: {results['success']}")
        print(f"❌ Failed updates: {results['failed']}")
        print(f"⚠️  Records not found in Airtable: {results['not_found']}")
        print(f"📝 Total CSV records processed: {results['total']}")
        
        if results['success'] > 0:
            print(f"\n🎉 {results['success']} Instagram avatars successfully added to Airtable!")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} updates failed. Check the logs for details.")
            
        if results['not_found'] > 0:
            print(f"\n🔍 {results['not_found']} CSV records couldn't be matched with Airtable records.")
            print("   Make sure your Airtable has 'id' or 'login' fields that match the CSV data.")
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()