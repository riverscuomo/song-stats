#!/usr/bin/env python
"""
Song Stats
A tool for collecting and analyzing song data from various sources
"""
import argparse
import logging
import sys
import os
from dotenv import load_dotenv

# Import modules
from modules.spotify_module import load_spotify_credentials, get_song_data
from modules.youtube_module import load_youtube_credentials, get_video_view_count
from modules.genius_module import load_genius_credentials, get_song_lyrics
from modules.sheets_module import load_sheets_credentials, get_sheet, get_all_records, update_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('songdata')

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
        sheets_client, _ = load_sheets_credentials(config)
        spotify_client = load_spotify_credentials(config) if "spotify" in methods else None
        youtube_client = load_youtube_credentials(config) if "youtube" in methods else None
        genius_client = load_genius_credentials(config) if "lyrics" in methods else None
    except Exception as e:
        logger.error(f"Error initializing API clients: {e}")
        return False
    
    try:
        # Get the sheet
        sheet = get_sheet(spreadsheet_name, worksheet_name, sheets_client)
        data = get_all_records(sheet)
        
        if start_row > 0:
            data = data[start_row:]
        
        if not data:
            logger.warning("No data found in sheet")
            return False
        
        logger.info(f"Found {len(data)} rows to process")
        
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
        
        # Update row with song data
        row['track_id'] = song_data.get('track_id', '')
        row['song_popularity'] = song_data.get('popularity', 0)
        row['duration_ms'] = song_data.get('duration_ms', 0)
        row['tempo'] = round(song_data.get('tempo', 0), 1)
        row['energy'] = round(song_data.get('energy', 0), 3)
        row['danceability'] = round(song_data.get('danceability', 0), 3)
        row['valence'] = round(song_data.get('valence', 0), 3)
        
        # Optional fields
        if 'genres' in row:
            row['genres'] = ', '.join(song_data.get('genres', []))
            
        if 'release_date' in row and not row.get('release_date'):
            row['release_date'] = song_data.get('album_release_date', '')
            
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
            
        # Get view count from YouTube
        view_count = get_video_view_count(artist_name, song_title, youtube_client)
        
        if view_count > 0:
            row['view_count'] = view_count
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
            
        # Get lyrics from Genius
        lyrics = get_song_lyrics(artist_name, song_title, genius_client)
        
        if lyrics:
            if 'lyrics' in row:
                row['lyrics'] = lyrics
                return True
            else:
                # Store lyrics length if lyrics field doesn't exist
                row['lyrics_length'] = len(lyrics)
                return True
        else:
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
