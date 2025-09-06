import os
import pickle
from datetime import datetime  # Add this import
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NamesToSheetsUploader:
    def __init__(self, spreadsheet_id, sheet_name="Sheet1"):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = self.authenticate_google_sheets()
    
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API"""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('sheets', 'v4', credentials=creds)
    
    def parse_names_txt(self, file_path):
        """Parse the names.txt file with flexible handling of optional description field"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
                # Skip header line
                for line_num, line in enumerate(lines[1:], 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Split by colon with no limit to handle all cases
                        parts = line.split(':')
                        
                        if len(parts) >= 6:  # Minimum required fields
                            # Detect format based on number of parts
                            if len(parts) == 6:  # Format: id:login:fol_cnt:post_cnt:name:avatar (no desc, no gender)
                                record = {
                                    'id': parts[0].strip(),
                                    'login': parts[1].strip(),
                                    'fol_cnt': parts[2].strip(),
                                    'post_cnt': parts[3].strip(),
                                    'name': parts[4].strip(),
                                    'desc': '',  # Empty description
                                    'avatar': parts[5].strip(),
                                    'gender': ''  # Empty gender
                                }
                            elif len(parts) == 7:  # Format: id:login:fol_cnt:post_cnt:name:avatar:gender (no desc)
                                record = {
                                    'id': parts[0].strip(),
                                    'login': parts[1].strip(),
                                    'fol_cnt': parts[2].strip(),
                                    'post_cnt': parts[3].strip(),
                                    'name': parts[4].strip(),
                                    'desc': '',  # Empty description
                                    'avatar': parts[5].strip(),
                                    'gender': parts[6].strip()
                                }
                            elif len(parts) == 8:  # Format: id:login:fol_cnt:post_cnt:name:desc:avatar:gender (full format)
                                record = {
                                    'id': parts[0].strip(),
                                    'login': parts[1].strip(),
                                    'fol_cnt': parts[2].strip(),
                                    'post_cnt': parts[3].strip(),
                                    'name': parts[4].strip(),
                                    'desc': parts[5].strip(),
                                    'avatar': parts[6].strip(),
                                    'gender': parts[7].strip()
                                }
                            else:  # More than 8 parts - assume colons in description
                                # Rejoin extra parts back into description
                                desc_parts = parts[5:-2]  # Everything between name and avatar
                                record = {
                                    'id': parts[0].strip(),
                                    'login': parts[1].strip(),
                                    'fol_cnt': parts[2].strip(),
                                    'post_cnt': parts[3].strip(),
                                    'name': parts[4].strip(),
                                    'desc': ':'.join(desc_parts).strip(),
                                    'avatar': parts[-2].strip(),
                                    'gender': parts[-1].strip()
                                }
                            
                            records.append(record)
                        else:
                            logger.warning(f"Line {line_num}: Invalid format, expected at least 6 fields but got {len(parts)}")
                    except Exception as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
        
        logger.info(f"Parsed {len(records)} records from {file_path}")
        return records
    
    def get_existing_logins(self):
        """Get existing login values from the sheet to avoid duplicates"""
        try:
            # Get the login column (column B, assuming standard order)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!B:B'
            ).execute()
            
            values = result.get('values', [])
            # Skip header row and extract login values
            existing_logins = set()
            for row in values[1:]:  # Skip header
                if row:  # Check if row is not empty
                    existing_logins.add(row[0].strip())
            
            logger.info(f"Found {len(existing_logins)} existing login values in sheet")
            return existing_logins
        
        except Exception as e:
            logger.error(f"Error getting existing logins: {e}")
            return set()
    
    def append_new_records(self, records):
        """Append only new records (not already in sheet by login) to the sheet"""
        existing_logins = self.get_existing_logins()
        new_records = [r for r in records if r['login'] not in existing_logins]
        
        if not new_records:
            logger.info("No new records to add - all logins already exist in sheet.")
            return 0
        
        # Convert records to rows
        rows = []
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get current date in YYYY-MM-DD format
        
        for record in new_records:
            rows.append([
                record['id'],
                record['login'],
                record['fol_cnt'],
                record['post_cnt'],
                record['name'],
                record['desc'],
                record['avatar'],
                record['gender'],
                current_date  # Add current date as 9th column
            ])
        
        # Append to sheet
        body = {'values': rows}
        
        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:I',  # Changed from A:G to A:I to include all 9 columns
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Successfully added {len(new_records)} new records to the sheet.")
            
            # Log some examples of what was added
            for i, record in enumerate(new_records[:5]):  # Show first 5
                logger.info(f"Added: {record['login']} - {record['name']}")
            
            if len(new_records) > 5:
                logger.info(f"... and {len(new_records) - 5} more records")
            
            return len(new_records)
        
        except Exception as e:
            logger.error(f"Error appending records: {e}")
            return 0
    
    def process_names_file(self, file_path=None):
        """Main method to process the names.txt file and append to sheets"""
        if file_path is None:
            file_path = r"c:\Users\felix\Scripts\names.txt"
        
        logger.info(f"Processing file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 0
        
        # Parse the txt file
        records = self.parse_names_txt(file_path)
        if not records:
            logger.error("No records parsed from file")
            return 0
        
        # Append new records
        added_count = self.append_new_records(records)
        
        logger.info(f"Process completed. Added {added_count} new records.")
        return added_count

# Usage example
if __name__ == "__main__":
    # Replace with your Google Sheets ID (from the URL)
    SPREADSHEET_ID = "1sxNbxXk4PJtWpf7w9kFANcgUr20yCi1bMkolXALDGHk"
    SHEET_NAME = "All Girls"  # Replace with your sheet name if different
    
    try:
        uploader = NamesToSheetsUploader(SPREADSHEET_ID, SHEET_NAME)
        
        # Process your names.txt file
        added_count = uploader.process_names_file()
        
        print(f"\n=== SUMMARY ===")
        print(f"Successfully processed names.txt")
        print(f"Added {added_count} new records to Google Sheets")
        print(f"Duplicates were automatically skipped based on login field")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")