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
    # More generic bad strings that appear in most Genius lyrics
    bad_strings = [
        "Embed", 
        "[", 
        "You might also like",
        "See",
        "Contributors",
        "Translations",
        "Read More",
        "Lyrics",
        "Romanization"
    ]
    lyrics_list = lyrics_string.split("\n")
    lyrics_list = [line for line in lyrics_list if not line.startswith(tuple(bad_strings))]
    return "\n".join(lyrics_list)


def remove_metadata_header(lyrics_string):
    """Remove metadata and header content that appears before the actual lyrics"""
    if not lyrics_string:
        return ""
    
    # Check for common Genius lyrics separator
    if "---" in lyrics_string:
        # Take only content after the first separator
        parts = lyrics_string.split("---", 1)
        if len(parts) > 1 and len(parts[1]) > 100:  # Make sure we didn't accidentally cut off lyrics
            return parts[1].strip()
    
    # Try to detect the actual lyrics by looking for longer meaningful sections
    lines = lyrics_string.split("\n")
    
    # Find the first line that likely begins the actual lyrics
    # (typically after the metadata, and doesn't contain common metadata words)
    metadata_indicators = [
        "Contributors", "Translations", "Lyrics", "Read More", "Released", 
        "Romanization", "EP", "music video", "album", "single", "track", "Music"
    ]
    
    # Find a clean starting point - look for a blank line followed by content
    # that doesn't match metadata patterns
    start_index = 0
    for i in range(len(lines)):
        # Skip very short lines, they're usually not the start of lyrics
        if not lines[i].strip() and i+1 < len(lines) and len(lines[i+1].strip()) > 5:
            # Check if the next line doesn't contain metadata indicators
            if not any(indicator in lines[i+1] for indicator in metadata_indicators):
                start_index = i + 1
                break
    
    # If we found a good starting point, use it
    if start_index > 0:
        cleaned_lyrics = "\n".join(lines[start_index:])
        
        # Extra check: if we have very little content left, revert to original
        if len(cleaned_lyrics) < 100 and len(lyrics_string) > 200:
            return lyrics_string
        return cleaned_lyrics
    
    return lyrics_string


def clean_lyrics(lyrics_string):
    """Apply all lyrics cleaning functions"""
    if not lyrics_string:
        return ""
    
    # First remove the metadata header
    lyrics = remove_metadata_header(lyrics_string)
    
    # Then apply other cleaning functions
    lyrics = remove_bgvs(lyrics)
    lyrics = remove_bad_lines(lyrics)
    
    # Additional cleaning
    lyrics = re.sub(r"\[.*?\]", "", lyrics)  # Remove square bracket content
    lyrics = re.sub(r"\d+ Contributors", "", lyrics)  # Remove contributor counts
    
    # Normalize newlines
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)  # Replace 3+ newlines with 2
    
    return lyrics.strip()


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
