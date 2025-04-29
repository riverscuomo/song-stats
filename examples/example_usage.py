"""
Example usage of the Song Stats toolkit
"""
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import using the proper package structure
from modules.spotify_module import load_spotify_credentials, get_song_data
from modules.youtube_module import get_video_view_count
from modules.genius_module import get_song_lyrics
from modules.sheets_module import load_sheets_credentials, get_sheet, get_all_records, update_range


def example_single_song():
    """Example of analyzing a single song"""
    artist_name = "Weezer"
    song_title = "Island In The Sun"
    
    print(f"\nGathering data for {artist_name} - {song_title}...")
    
    # Get Spotify data
    try:
        spotify_client = load_spotify_credentials()
        song_data = get_song_data(artist_name, song_title, spotify_client)
        print("\nSpotify Data:")
        print(f"Track ID: {song_data.get('track_id')}")
        print(f"Popularity: {song_data.get('popularity')}")
        print(f"Album: {song_data.get('album_name')}")
        print(f"Release Date: {song_data.get('album_release_date')}")
        print(f"Tempo: {song_data.get('tempo')}")
        print(f"Energy: {song_data.get('energy')}")
        print(f"Danceability: {song_data.get('danceability')}")
        print(f"Duration: {int(song_data.get('duration_ms', 0) / 1000)} seconds")
    except Exception as e:
        print(f"Error getting Spotify data: {e}")
    
    # Get YouTube data
    try:
        youtube_client = None  # Will be loaded from .env
        view_count = get_video_view_count(artist_name, song_title)
        print("\nYouTube Data:")
        print(f"View Count: {view_count:,}")
    except Exception as e:
        print(f"Error getting YouTube data: {e}")
    
    # Get lyrics
    try:
        genius_client = None  # Will be loaded from .env
        lyrics = get_song_lyrics(artist_name, song_title)
        print("\nLyrics Preview:")
        print(f"{lyrics[:150]}...")
        print(f"Lyrics Length: {len(lyrics)} characters")
    except Exception as e:
        print(f"Error getting lyrics: {e}")


def example_update_spreadsheet():
    """Example of updating a Google Sheet"""
    try:
        # Get sheet
        sheets_client, _ = load_sheets_credentials()
        sheet = get_sheet("My Song Collection", 0, sheets_client)
        data = get_all_records(sheet)
        
        print(f"\nFound {len(data)} songs in spreadsheet")
        
        # Process first 3 rows only for this example
        for i, row in enumerate(data[:3]):
            artist_name = row.get('artist_name')
            song_title = row.get('song_title')
            
            if not artist_name or not song_title:
                continue
                
            print(f"\nProcessing {artist_name} - {song_title}")
            
            # Get and update Spotify data
            spotify_client = load_spotify_credentials()
            song_data = get_song_data(artist_name, song_title, spotify_client)
            
            if song_data:
                row['track_id'] = song_data.get('track_id', '')
                row['song_popularity'] = song_data.get('popularity', 0)
                row['duration'] = int(song_data.get('duration_ms', 0) / 1000)  # Convert to seconds
                row['tempo_spotify'] = round(song_data.get('tempo', 0), 1)
                row['energy'] = round(song_data.get('energy', 0), 3)
                row['danceability'] = round(song_data.get('danceability', 0), 3)
                row['artist_id'] = song_data.get('artist_id', '')
                row['year'] = song_data.get('album_release_date', '')[:4]  # Just the year
                print(f"Updated Spotify data: Popularity={row['song_popularity']}, Tempo={row['tempo_spotify']}")
            
            # Get and update YouTube data
            view_count = get_video_view_count(artist_name, song_title)
            if view_count > 0:
                row['youtube_views'] = view_count
                print(f"Updated YouTube views: {view_count:,}")
        
        # Update the first 3 rows
        print("\nUpdating spreadsheet...")
        update_range(sheet, data[:3], start_row=2)
        print("Spreadsheet updated!")
        
    except Exception as e:
        print(f"Error in spreadsheet example: {e}")


if __name__ == "__main__":
    print("Song Stats Toolkit - Example Usage")
    print("==================================")
    
    example_single_song()
    
    print("\n\nPress Enter to run the spreadsheet example (requires valid Google credentials)...")
    input()
    
    example_update_spreadsheet()
