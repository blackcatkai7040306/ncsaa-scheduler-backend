"""
Test Google Sheets credentials to diagnose authentication issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_google_credentials, SPREADSHEET_ID
import gspread

def test_credentials():
    """Test if credentials are valid and can access the spreadsheet."""
    print("=" * 80)
    print("TESTING GOOGLE SHEETS CREDENTIALS")
    print("=" * 80)
    
    try:
        print("\n[1/4] Loading credentials...")
        credentials = get_google_credentials()
        print("[OK] Credentials loaded successfully")
        print(f"    Service account email: {credentials.service_account_email}")
        
        print("\n[2/4] Creating gspread client...")
        client = gspread.authorize(credentials)
        print("[OK] Client authorized successfully")
        
        print(f"\n[3/4] Attempting to open spreadsheet: {SPREADSHEET_ID}")
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print(f"[OK] Spreadsheet opened successfully")
        print(f"    Title: {spreadsheet.title}")
        
        print("\n[4/4] Listing worksheets...")
        worksheets = spreadsheet.worksheets()
        print(f"[OK] Found {len(worksheets)} worksheets:")
        for ws in worksheets:
            print(f"    - {ws.title}")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] ALL TESTS PASSED - Credentials are working correctly!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"    {str(e)}")
        
        print("\n" + "=" * 80)
        print("TROUBLESHOOTING STEPS:")
        print("=" * 80)
        
        if "invalid_grant" in str(e).lower() or "invalid jwt" in str(e).lower():
            print("""
1. The service account credentials are invalid or have been revoked.
   
   SOLUTION:
   a) Go to Google Cloud Console: https://console.cloud.google.com
   b) Navigate to: IAM & Admin > Service Accounts
   c) Find your service account: sheet-reader@ncsaa-484512.iam.gserviceaccount.com
   d) Check if it's enabled (not disabled/deleted)
   e) Create a NEW key:
      - Click on the service account
      - Go to "Keys" tab
      - Click "Add Key" > "Create new key"
      - Choose JSON format
      - Download the new key
   f) Replace the credentials file with the new key
   
2. Make sure the service account has access to the Google Sheet:
   a) Open your Google Sheet
   b) Click "Share" button
   c) Add: sheet-reader@ncsaa-484512.iam.gserviceaccount.com
   d) Give it "Editor" or "Viewer" permissions
""")
        
        elif "403" in str(e) or "permission" in str(e).lower():
            print("""
The service account doesn't have permission to access the spreadsheet.

SOLUTION:
1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}
2. Click the "Share" button (top right)
3. Add this email: sheet-reader@ncsaa-484512.iam.gserviceaccount.com
4. Give it "Editor" permissions
5. Click "Send"
""")
        
        elif "404" in str(e) or "not found" in str(e).lower():
            print(f"""
The spreadsheet with ID '{SPREADSHEET_ID}' was not found.

SOLUTION:
1. Verify the spreadsheet ID in your .env file or config.py
2. Make sure the spreadsheet exists and hasn't been deleted
3. Check that you're using the correct Google account
""")
        
        else:
            print("""
Unknown error. Please check:
1. Your internet connection
2. Google Sheets API is enabled in your Google Cloud project
3. The credentials file is not corrupted
""")
        
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_credentials()
    sys.exit(0 if success else 1)
