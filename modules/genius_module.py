"""
Genius Lyrics API Module
Provides functionality for retrieving and processing song lyrics from Genius
"""
import lyricsgenius
import re
import os
from dotenv import load_dotenv

def load_genius_credentials(config=None):
    """
    Load Genius API credentials either from config or environment variables
    
    Args:
        config: Optional configuration object with credentials
        
    Returns:
        Genius API client
    """
    if config and hasattr(config, 'GENIUS_ACCESS_TOKEN'):
        access_token = config.GENIUS_ACCESS_TOKEN
    else:
        # Try to load from environment
        load_dotenv()
        access_token = os.getenv("GENIUS_ACCESS_TOKEN")
        
    if not access_token:
        raise ValueError("Genius API access token not found. Please set GENIUS_ACCESS_TOKEN in your .env file or config.")
        
    return lyricsgenius.Genius(access_token)


def remove_bgvs(lyrics_string):
    """Remove background vocals (text in parentheses) from lyrics"""
    lyrics_string = re.sub(r"\([^)]*\)", "", lyrics_string)
    if "\n\n" in lyrics_string:
        lyrics_string = lyrics_string.replace("\n\n\n", "\n\n")
    return lyrics_string


def remove_bad_lines(lyrics_string):
    """Remove any lines that start with certain bad strings"""
    bad_strings = ["See Weezer Live", "Embed", "[", "You might also like"]
    lyrics_list = lyrics_string.split("\n")
    lyrics_list = [line for line in lyrics_list if not line.startswith(tuple(bad_strings))]
    return "\n".join(lyrics_list)


def clean_lyrics(lyrics_string):
    """Apply all lyrics cleaning functions"""
    if not lyrics_string:
        return ""
    
    lyrics = remove_bgvs(lyrics_string)
    lyrics = remove_bad_lines(lyrics)
    return lyrics


def get_song_lyrics(artist_name, song_title, genius_client=None):
    """
    Get lyrics for a specific song
    
    Args:
        artist_name: Name of the artist
        song_title: Title of the song
        genius_client: Optional pre-configured Genius client
        
    Returns:
        Cleaned lyrics as string or empty string if not found
    """
    if not genius_client:
        genius_client = load_genius_credentials()
    
    try:
        song = genius_client.search_song(song_title, artist_name)
        if song:
            return clean_lyrics(song.lyrics)
    except Exception as e:
        print(f"Error retrieving lyrics for {artist_name} - {song_title}: {e}")
    
    return ""
