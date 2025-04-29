"""
Google Sheets Module
Provides functionality for reading and updating Google Sheets
"""
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

def load_sheets_credentials(config=None, credentials_path=None):
    """
    Load Google Sheets API credentials either from config or file path
    
    Args:
        config: Optional configuration object with credentials path
        credentials_path: Optional path to service account JSON
        
    Returns:
        Google Sheets client and credentials
    """
    if credentials_path:
        creds_file = credentials_path
    elif config and hasattr(config, 'GOOGLE_SHEETS_CREDENTIALS_FILE'):
        creds_file = config.GOOGLE_SHEETS_CREDENTIALS_FILE
    else:
        # Try to load from environment
        load_dotenv()
        creds_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
        
    if not creds_file or not os.path.exists(creds_file):
        raise ValueError("Google Sheets credentials file not found. Please set GOOGLE_SHEETS_CREDENTIALS_FILE in your .env file or config.")
    
    # Define the scope
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Authenticate
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    
    return client, creds


def get_sheet(spreadsheet_name, worksheet_name, client=None, credentials_path=None):
    """
    Get a specific worksheet from a Google Spreadsheet
    
    Args:
        spreadsheet_name: Name of the spreadsheet
        worksheet_name: Name of the worksheet (or index)
        client: Optional pre-configured gspread client
        credentials_path: Optional path to service account JSON if client not provided
        
    Returns:
        Worksheet object
    """
    if not client:
        client, _ = load_sheets_credentials(credentials_path=credentials_path)
    
    try:
        # Open spreadsheet
        spreadsheet = client.open(spreadsheet_name)
        
        # Get worksheet by name or index
        if isinstance(worksheet_name, int):
            worksheet = spreadsheet.get_worksheet(worksheet_name)
        else:
            worksheet = spreadsheet.worksheet(worksheet_name)
            
        return worksheet
    except Exception as e:
        print(f"Error accessing Google Sheet {spreadsheet_name}/{worksheet_name}: {e}")
        raise


def get_all_records(sheet):
    """
    Get all records from a worksheet as a list of dictionaries
    
    Args:
        sheet: Worksheet object
        
    Returns:
        List of dictionaries with row data
    """
    try:
        return sheet.get_all_records()
    except Exception as e:
        print(f"Error getting records from sheet: {e}")
        return []


def update_range(sheet, data, start_row=2, start_col=1):
    """
    Update multiple rows in a worksheet
    
    Args:
        sheet: Worksheet object
        data: List of dictionaries with row data
        start_row: Starting row index (1-based)
        start_col: Starting column index (1-based)
        
    Returns:
        None
    """
    if not data:
        return
    
    try:
        # Get column headers
        headers = sheet.row_values(1)
        
        # Prepare values to update
        rows_to_update = []
        
        for i, row_dict in enumerate(data):
            row = []
            for header in headers:
                if header in row_dict:
                    row.append(row_dict[header])
                else:
                    # If key doesn't exist in this row, add empty string
                    row.append("")
            rows_to_update.append(row)
        
        # Update the range
        if rows_to_update:
            end_row = start_row + len(rows_to_update) - 1
            end_col = start_col + len(headers) - 1
            cell_range = sheet.range(start_row, start_col, end_row, end_col)
            
            # Fill in the values
            for i, cell in enumerate(cell_range):
                row_idx = i // len(headers)
                col_idx = i % len(headers)
                cell.value = rows_to_update[row_idx][col_idx]
            
            # Update in batch
            sheet.update_cells(cell_range)
    except Exception as e:
        print(f"Error updating sheet: {e}")


def find_row_by_values(sheet, search_dict):
    """
    Find row indices that match given criteria
    
    Args:
        sheet: Worksheet object
        search_dict: Dictionary with column names and values to search for
        
    Returns:
        List of matching row indices (0-based)
    """
    all_records = get_all_records(sheet)
    matching_indices = []
    
    for i, record in enumerate(all_records):
        match = True
        for key, value in search_dict.items():
            if key not in record or record[key] != value:
                match = False
                break
        if match:
            matching_indices.append(i + 2)  # +2 because records are 0-based but sheet is 1-based with header
    
    return matching_indices
