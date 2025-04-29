"""
Spotify Module
Provides functionality for retrieving song and artist data from Spotify
"""
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

def load_spotify_credentials(config=None):
    """
    Load Spotify API credentials either from config or environment variables
    
    Args:
        config: Optional configuration object with credentials
        
    Returns:
        Spotify API client
    """
    if config and hasattr(config, 'SPOTIFY_CLIENT_ID') and hasattr(config, 'SPOTIFY_CLIENT_SECRET'):
        client_id = config.SPOTIFY_CLIENT_ID
        client_secret = config.SPOTIFY_CLIENT_SECRET
    else:
        # Try to load from environment
        load_dotenv()
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
    if not client_id or not client_secret:
        raise ValueError("Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file or config.")
        
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def search_spotify_track(artist_name, song_title, spotify_client=None):
    """
    Search for a track on Spotify
    
    Args:
        artist_name: Name of the artist
        song_title: Title of the song
        spotify_client: Optional pre-configured Spotify client
        
    Returns:
        Dict with track information or None if not found
    """
    if not spotify_client:
        spotify_client = load_spotify_credentials()
    
    try:
        # Format search query
        search_query = f"track:{song_title} artist:{artist_name}"
        result = spotify_client.search(search_query, type="track", limit=1)
        
        if result["tracks"]["items"]:
            return result["tracks"]["items"][0]
    except Exception as e:
        print(f"Error searching Spotify for {artist_name} - {song_title}: {e}")
    
    return None


def get_track_features(track_id, spotify_client=None):
    """
    Get audio features for a specific track
    
    Args:
        track_id: Spotify track ID
        spotify_client: Optional pre-configured Spotify client
        
    Returns:
        Dict with audio features or empty dict if not found
    """
    if not spotify_client:
        spotify_client = load_spotify_credentials()
    
    if not track_id:
        return {}
    
    try:
        features = spotify_client.audio_features([track_id])[0]
        return features
    except Exception as e:
        print(f"Error getting audio features for track {track_id}: {e}")
    
    return {}


def get_artist_info(artist_id, spotify_client=None):
    """
    Get artist information including genres
    
    Args:
        artist_id: Spotify artist ID
        spotify_client: Optional pre-configured Spotify client
        
    Returns:
        Dict with artist information or empty dict if not found
    """
    if not spotify_client:
        spotify_client = load_spotify_credentials()
    
    if not artist_id:
        return {}
    
    try:
        artist = spotify_client.artist(artist_id)
        return artist
    except Exception as e:
        print(f"Error getting artist info for {artist_id}: {e}")
    
    return {}


def get_song_data(artist_name, song_title, spotify_client=None):
    """
    Get comprehensive song data including track details, audio features, and artist info
    
    Args:
        artist_name: Name of the artist
        song_title: Title of the song
        spotify_client: Optional pre-configured Spotify client
        
    Returns:
        Dict with song data or empty dict if not found
    """
    if not spotify_client:
        spotify_client = load_spotify_credentials()
    
    # Search for the track
    track_data = search_spotify_track(artist_name, song_title, spotify_client)
    
    if not track_data:
        return {}
    
    # Get track ID and artist ID
    track_id = track_data["id"]
    artist_id = track_data["artists"][0]["id"]
    
    # Get audio features and artist info
    audio_features = get_track_features(track_id, spotify_client)
    artist_info = get_artist_info(artist_id, spotify_client)
    
    # Compile all data
    return {
        "track_id": track_id,
        "track_name": track_data["name"],
        "artist_id": artist_id,
        "artist_name": track_data["artists"][0]["name"],
        "popularity": track_data.get("popularity", 0),
        "duration_ms": track_data.get("duration_ms", 0),
        "album_name": track_data.get("album", {}).get("name", ""),
        "album_release_date": track_data.get("album", {}).get("release_date", ""),
        "tempo": audio_features.get("tempo", 0),
        "energy": audio_features.get("energy", 0),
        "danceability": audio_features.get("danceability", 0),
        "valence": audio_features.get("valence", 0),
        "loudness": audio_features.get("loudness", 0),
        "genres": artist_info.get("genres", [])
    }
