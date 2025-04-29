"""
YouTube Module
Provides functionality for retrieving YouTube video statistics
"""
import os
import re
import googleapiclient.discovery
from dotenv import load_dotenv

def load_youtube_credentials(config=None):
    """
    Load YouTube API credentials either from config or environment variables
    
    Args:
        config: Optional configuration object with credentials
        
    Returns:
        YouTube API client
    """
    if config and hasattr(config, 'YOUTUBE_API_KEY'):
        api_key = config.YOUTUBE_API_KEY
    else:
        # Try to load from environment
        load_dotenv()
        api_key = os.getenv("YOUTUBE_API_KEY")
        
    if not api_key:
        raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file or config.")
        
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)


def search_youtube_video(artist_name, song_title, youtube_client=None):
    """
    Search for a music video on YouTube
    
    Args:
        artist_name: Name of the artist
        song_title: Title of the song
        youtube_client: Optional pre-configured YouTube client
        
    Returns:
        Video ID or None if not found
    """
    if not youtube_client:
        youtube_client = load_youtube_credentials()
    
    try:
        # Search for the song with the artist name
        search_query = f"{artist_name} {song_title} official video"
        request = youtube_client.search().list(
            q=search_query,
            part="id,snippet",
            maxResults=5,
            type="video"
        )
        response = request.execute()
        
        # Return the first video ID found
        if response.get("items"):
            return response["items"][0]["id"]["videoId"]
    except Exception as e:
        print(f"Error searching YouTube for {artist_name} - {song_title}: {e}")
    
    return None


def get_video_statistics(video_id, youtube_client=None):
    """
    Get statistics for a YouTube video
    
    Args:
        video_id: YouTube video ID
        youtube_client: Optional pre-configured YouTube client
        
    Returns:
        Dict containing video statistics or empty dict if not found
    """
    if not youtube_client:
        youtube_client = load_youtube_credentials()
    
    if not video_id:
        return {}
        
    try:
        request = youtube_client.videos().list(
            part="statistics,snippet",
            id=video_id
        )
        response = request.execute()
        
        if response.get("items"):
            stats = response["items"][0]["statistics"]
            stats["title"] = response["items"][0]["snippet"]["title"]
            stats["published_at"] = response["items"][0]["snippet"]["publishedAt"]
            return stats
    except Exception as e:
        print(f"Error getting YouTube statistics for video {video_id}: {e}")
    
    return {}


def get_video_view_count(artist_name, song_title, youtube_client=None):
    """
    Get view count for a song's YouTube video
    
    Args:
        artist_name: Name of the artist
        song_title: Title of the song
        youtube_client: Optional pre-configured YouTube client
        
    Returns:
        View count as integer or 0 if not found
    """
    if not youtube_client:
        youtube_client = load_youtube_credentials()
    
    video_id = search_youtube_video(artist_name, song_title, youtube_client)
    if not video_id:
        return 0
    
    stats = get_video_statistics(video_id, youtube_client)
    return int(stats.get("viewCount", 0))
