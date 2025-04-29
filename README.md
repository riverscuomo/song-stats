# Song Stats Toolkit

A Python toolkit for collecting and analyzing song data from various music platforms. This toolkit allows you to:

- Get song popularity, audio features, and metadata from Spotify
- Retrieve view counts from YouTube
- Find and clean song lyrics from Genius
- Store and update all data in Google Sheets

## Features

- **Spotify Integration**: Get song popularity, tempo, energy, danceability, and more
- **YouTube Stats**: Look up view counts for music videos
- **Lyrics Retrieval**: Get cleaned lyrics from Genius
- **Google Sheets Integration**: Read and update song data in spreadsheets

## Installation

1. Clone this repository

2. Set up a virtual environment (recommended):

   **Windows:**

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS/Linux:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:

   ```powershell
   pip install -r requirements.txt
   ```

4. Set up your API credentials (see Configuration section)

## Configuration

You can configure the toolkit in two ways:

### Option 1: Environment variables (.env file)

Create a `.env` file in the project root with the following variables:

```ini
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GENIUS_ACCESS_TOKEN=your_genius_token
YOUTUBE_API_KEY=your_youtube_key
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
```

### Option 2: Python config file

Copy `config_example.py` to `config.py` and fill in your credentials:

```python
SPOTIFY_CLIENT_ID = "your_spotify_client_id"
SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
GENIUS_ACCESS_TOKEN = "your_genius_token"
YOUTUBE_API_KEY = "your_youtube_key"
GOOGLE_SHEETS_CREDENTIALS_FILE = "path/to/credentials.json"
```

## Google Sheets Setup

1. Create a Google Sheet with at minimum these columns:
   - `artist_name` (required)
   - `song_title` (required)
   - Additional columns will be populated: `track_id`, `song_popularity`, `duration`, `tempo_spotify`, `energy`, `danceability`, `artist_id`, `year`, `youtube_views`, `lyrics`, etc.

2. Share your Google Sheet with the email address from your service account credentials. Give it the role of "Editor".

## Usage

### Basic Command Line Usage

```bash
python songdata.py "Your Spreadsheet Name" "Sheet1" --methods spotify youtube lyrics
```

### Options

- `spreadsheet`: Name of your Google Sheet
- `worksheet`: Name or index of the worksheet (0 for first sheet)
- `--methods`: Data to collect (spotify, youtube, lyrics, or any combination)
- `--start-row`: Row to start from (0-based, after headers)
- `--config`: Path to config file if using Option 2 for configuration

### Example

```bash
python songdata.py "Weezer Setlist" 0 --methods spotify youtube
```

## Using as a Module

You can also import and use the toolkit in your own Python scripts. See the examples directory for sample code.

## API Requirements

You'll need to set up accounts and obtain API keys for:

1. [Spotify Developer Account](https://developer.spotify.com/dashboard/)
2. [Genius API](https://genius.com/api-clients)
3. [YouTube Data API](https://console.developers.google.com/)
4. [Google Sheets API](https://console.cloud.google.com/)
