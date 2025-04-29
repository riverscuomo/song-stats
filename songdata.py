#!/usr/bin/env python
"""
Song Stats
A tool for collecting and analyzing song data from various sources
"""
import argparse
import logging
import sys

# Import modules
from modules.spotify_module import load_spotify_credentials, get_song_data
from modules.youtube_module import load_youtube_credentials, get_video_view_count
from modules.genius_module import load_genius_credentials, get_song_lyrics
from modules.sheets_module import load_sheets_credentials, get_sheet, get_all_records, update_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('songdata')

# Set to display all INFO messages
logger.setLevel(logging.INFO)
logger.info("Song Stats starting up...")

def ensure_required_headers(sheet, methods):
    """
    Check if all required headers exist in the sheet and add any missing ones
    
    Args:
        sheet: Worksheet object
        methods: List of data collection methods to run
        
    Returns:
        Boolean indicating if headers were updated
    """
    # Get existing headers
    try:
        existing_headers = sheet.row_values(1)
        logger.info(f"Existing headers: {existing_headers}")
        
        # Define required headers for each method
        required_headers = {
            'base': ['artist_name', 'song_title'],
            'spotify': ['track_id', 'song_popularity', 'duration', 'tempo_spotify', 'energy', 'danceability', 'artist_id', 'year'],
            'youtube': ['youtube_views'],
            'lyrics': ['lyrics']
        }
        
        # Check which headers are missing
        missing_headers = []
        
        # Base headers are always required
        for header in required_headers['base']:
            if header not in existing_headers:
                missing_headers.append(header)
        
        # Method-specific headers
        for method in methods:
            if method in required_headers:
                for header in required_headers[method]:
                    if header not in existing_headers:
                        missing_headers.append(header)
        
        if missing_headers:
            logger.info(f"Adding missing headers: {missing_headers}")
            
            # Add missing headers
            new_headers = existing_headers + missing_headers
            sheet.update_cell(1, len(existing_headers) + 1, missing_headers[0])
            
            # We need to do this one by one to avoid rate limits
            for i, header in enumerate(missing_headers[1:], 1):
                sheet.update_cell(1, len(existing_headers) + i + 1, header)
                
            logger.info(f"Added {len(missing_headers)} missing headers to the sheet")
            return True
        else:
            logger.info("All required headers are present in the sheet")
            return False
            
    except Exception as e:
        logger.error(f"Error checking/updating headers: {e}")
        # Continue even if we can't add headers
        return False


def process_spreadsheet(spreadsheet_name, worksheet_name, methods, start_row=0, config=None):
    """
    Process a Google Sheet with song data
    
    Args:
        spreadsheet_name: Name of the Google Sheet
        worksheet_name: Name or index of the worksheet
        methods: List of data collection methods to run
        start_row: Row to start processing from (0-based, after headers)
        config: Optional configuration object
        
    Returns:
        True if updates were made, False otherwise
    """
    logger.info(f"Processing spreadsheet: {spreadsheet_name}, worksheet: {worksheet_name}")
    
    # Initialize API clients
    try:
        logger.info("Loading API credentials...")
        
        # Load Google Sheets credentials first since this is critical
        logger.info("Loading Google Sheets credentials...")
        try:
            sheets_client, _ = load_sheets_credentials(config)
            logger.info("Successfully connected to Google Sheets API")
        except Exception as sheets_error:
            logger.error(f"Failed to connect to Google Sheets: {sheets_error}")
            logger.error("Check your GOOGLE_SHEETS_CREDENTIALS_FILE path and file contents")
            return False
            
        # Load other API clients
        if "spotify" in methods:
            try:
                spotify_client = load_spotify_credentials(config)
                logger.info("Successfully connected to Spotify API")
            except Exception as spotify_error:
                logger.error(f"Failed to connect to Spotify API: {spotify_error}")
                spotify_client = None
                
        if "youtube" in methods:
            try:
                youtube_client = load_youtube_credentials(config) 
                logger.info("Successfully connected to YouTube API")
            except Exception as youtube_error:
                logger.error(f"Failed to connect to YouTube API: {youtube_error}")
                youtube_client = None
                
        if "lyrics" in methods:
            try:
                genius_client = load_genius_credentials(config)
                logger.info("Successfully connected to Genius API")
            except Exception as genius_error:
                logger.error(f"Failed to connect to Genius API: {genius_error}")
                genius_client = None
                
    except Exception as e:
        logger.error(f"Error initializing API clients: {e}")
        return False
    
    try:
        # Get the sheet
        logger.info(f"Attempting to access Google Sheet: '{spreadsheet_name}', worksheet: '{worksheet_name}'")
        try:
            sheet = get_sheet(spreadsheet_name, worksheet_name, sheets_client)
            logger.info(f"Successfully accessed the sheet")
            
            # Ensure all required headers exist
            logger.info("Checking for required headers...")
            ensure_required_headers(sheet, methods)
            
        except Exception as sheet_error:
            logger.error(f"Failed to access the sheet: {sheet_error}")
            logger.error("Check if the spreadsheet exists and is shared with your Google service account")
            return False
            
        # Get all records
        try:
            data = get_all_records(sheet)
            logger.info(f"Retrieved data from sheet (raw row count: {len(data)})")
        except Exception as data_error:
            logger.error(f"Failed to get records from sheet: {data_error}")
            return False
        
        if start_row > 0:
            data = data[start_row:]
            logger.info(f"Starting from row {start_row}, {len(data)} rows remaining")
        
        if not data:
            logger.warning("No data found in sheet")
            return False
        
        # Print some sample data to verify content
        logger.info(f"Found {len(data)} rows to process")
        if len(data) > 0:
            logger.info(f"First row preview: {data[0]}")
            
        # Check for required columns
        for row in data[:1]:  # Check just the first row
            if 'artist_name' not in row or 'song_title' not in row:
                logger.error("Missing required columns! Sheet must have 'artist_name' and 'song_title' columns.")
                return False
        
        # Track if updates were made
        updated = False
        
        # Process each row
        for i, row in enumerate(data):
            logger.info(f"Processing row {i+start_row+2}: {row.get('artist_name', '')} - {row.get('song_title', '')}")
            
            # Check if required fields exist
            if not row.get('artist_name') or not row.get('song_title'):
                logger.warning(f"Missing artist_name or song_title in row {i+start_row+2}, skipping")
                continue
            
            # Run requested methods
            if "spotify" in methods:
                updated = update_spotify_data(row, spotify_client) or updated
                
            if "youtube" in methods:
                updated = update_youtube_data(row, youtube_client) or updated
                
            if "lyrics" in methods:
                updated = update_lyrics_data(row, genius_client) or updated
        
        # Update the sheet if changes were made
        if updated:
            logger.info("Updating spreadsheet with new data")
            update_range(sheet, data, start_row=start_row+2)  # +2 for 1-based index and header row
            
        return updated
        
    except Exception as e:
        logger.error(f"Error processing spreadsheet: {e}")
        return False


def update_spotify_data(row, spotify_client):
    """Update row with Spotify data"""
    try:
        artist_name = row.get('artist_name', '').strip()
        song_title = row.get('song_title', '').strip()
        
        if not artist_name or not song_title:
            return False
            
        # Get song data from Spotify
        song_data = get_song_data(artist_name, song_title, spotify_client)
        
        if not song_data:
            logger.warning(f"No Spotify data found for {artist_name} - {song_title}")
            return False
        
        # Update row with song data - using original field names
        row['track_id'] = song_data.get('track_id', '')
        row['song_popularity'] = song_data.get('popularity', 0)
        row['duration'] = int(song_data.get('duration_ms', 0) / 1000)  # Convert to seconds
        row['tempo_spotify'] = round(song_data.get('tempo', 0), 1)
        row['energy'] = round(song_data.get('energy', 0), 3)
        row['danceability'] = round(song_data.get('danceability', 0), 3)
        
        # Set the artist_id (important for other functions)
        if 'artist_id' in row and not row.get('artist_id'):
            row['artist_id'] = song_data.get('artist_id', '')
        
        # Optional fields
        if 'genres' in row and not row.get('genres'):
            row['genres'] = str(song_data.get('genres', []))  # Format as string like original
            
        if 'year' in row and not row.get('year'):
            release_date = song_data.get('album_release_date', '')
            # Just take the year as in the original script
            if release_date and len(release_date) >= 4:
                row['year'] = release_date[:4]
            
        return True
    except Exception as e:
        logger.error(f"Error updating Spotify data: {e}")
        return False


def update_youtube_data(row, youtube_client):
    """Update row with YouTube data"""
    try:
        artist_name = row.get('artist_name', '').strip()
        song_title = row.get('song_title', '').strip()
        
        if not artist_name or not song_title:
            return False
            
        # Check if this is a cover (original script skipped covers)
        if row.get('cover', '').lower() == 'x':
            logger.info(f"Skipping YouTube data for cover song: {artist_name} - {song_title}")
            row['youtube_views'] = ""
            return False
            
        # Get view count from YouTube
        view_count = get_video_view_count(artist_name, song_title, youtube_client)
        
        if view_count > 0:
            # Use youtube_views field name as in original script
            row['youtube_views'] = view_count
            logger.info(f"Updated YouTube views for {song_title}: {view_count:,}")
            return True
        else:
            logger.warning(f"No YouTube data found for {artist_name} - {song_title}")
            return False
    except Exception as e:
        logger.error(f"Error updating YouTube data: {e}")
        return False


def update_lyrics_data(row, genius_client):
    """Update row with lyrics data"""
    try:
        artist_name = row.get('artist_name', '').strip()
        song_title = row.get('song_title', '').strip()
        
        if not artist_name or not song_title:
            return False
        
        # Only update empty or missing lyrics (like original script)
        if row.get('lyrics') not in ["", "!", None]:
            logger.info(f"Lyrics already exist for {artist_name} - {song_title}, skipping")
            return False
            
        # Get lyrics from Genius
        logger.info(f"Looking up lyrics for {artist_name} - {song_title} on Genius")
        lyrics = get_song_lyrics(artist_name, song_title, genius_client)
        
        if lyrics:
            # Check for maximum cell size limit (from original script)
            if len(lyrics) > 5000:
                lyrics = f'{artist_name}: {song_title}: Your input contains more than the maximum of 50000 characters in a single cell.'
                
            row['lyrics'] = lyrics
            logger.info(f"Found lyrics for {artist_name} - {song_title} ({len(lyrics)} characters)")
            return True
        else:
            # Original script used "!" to mark failed lyrics lookups
            row['lyrics'] = "!"
            logger.warning(f"No lyrics found for {artist_name} - {song_title}")
            return False
    except Exception as e:
        logger.error(f"Error updating lyrics data: {e}")
        return False


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Collect and analyze song data')
    parser.add_argument('spreadsheet', help='Google Sheet name')
    parser.add_argument('worksheet', help='Worksheet name or index')
    parser.add_argument('--methods', nargs='+', default=['spotify', 'youtube', 'lyrics'],
                        help='Data collection methods to run (spotify, youtube, lyrics)')
    parser.add_argument('--start-row', type=int, default=0,
                        help='Row to start processing from (0-based, after headers)')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Print out the arguments for debugging
    logger.info(f"Command line arguments:")
    logger.info(f"  Spreadsheet: {args.spreadsheet}")
    logger.info(f"  Worksheet: {args.worksheet}")
    logger.info(f"  Methods: {args.methods}")
    logger.info(f"  Start row: {args.start_row}")
    logger.info(f"  Config: {args.config}")
    
    
    # Load configuration if provided
    config = None
    if args.config:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", args.config)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return 1
    
    # Process the spreadsheet
    success = process_spreadsheet(
        args.spreadsheet, 
        args.worksheet, 
        args.methods,
        args.start_row,
        config
    )
    
    if success:
        logger.info("Processing completed successfully")
        return 0
    else:
        logger.warning("Processing completed with warnings or errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
