# Board Crawler

A Python tool for extracting content and metadata from Getty Images boards. The crawler fetches comprehensive information about each asset in a board, including creation dates, captions, licensing info, and other metadata.

## What it does

The crawler:
1. Takes a Getty Images board URL
2. Fetches the list of assets in that board
3. Gets detailed metadata for each asset
4. Saves the information to a CSV file
5. Only adds new assets when run multiple times

## Data collected

For each asset, the crawler captures:
- Basic info (ID, title, caption)
- Dates (created, submitted, added to board)
- Source info (artist, collection)
- Asset details (type, family, license type)
- Technical info (video status, preview URLs)
- Release information
- Board context (board ID, source URL)

## Setup

1. Make sure you have Python 3.6 or newer installed

2. Set up a virtual environment:

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install requests beautifulsoup4
```

## Usage

1. Download `board_crawler.py`

2. Edit the URLs list in the script:
```python
urls = [
    "https://www.gettyimages.com/collaboration/boards/YOUR-BOARD-ID",
    # Add more Getty Images board URLs here
]
```

3. Run the script (make sure your virtualenv is activated):
```bash
python board_crawler.py
```

The crawler will:
- Create `board_data.csv` in the same directory
- Show progress in the terminal
- Skip any assets it has already processed
- Handle errors gracefully

## Output Format

The CSV file includes these columns:
- `board_id`: Identifier for the Getty board
- `asset_id`: Unique identifier for the asset
- `title`: Asset title
- `caption`: Full description of the asset
- `date_created`: Original creation date
- `date_submitted`: When added to Getty
- `artist`: Creator/photographer
- `collection_name`: Getty collection name
- `asset_family`: Editorial/Creative
- `asset_type`: Type of content
- `license_type`: Licensing information
- `is_video`: Whether it's a video
- `release_info`: Usage rights information
- `preview_url`: URL to preview image
- Added info:
  - `added_by_id`: User who added to board
  - `added_date`: When added to board
  - `source_url`: Original board URL

## Incremental Updates

The crawler is designed to be run multiple times on the same board(s). It will:
1. Check for existing CSV file
2. Load list of processed assets
3. Only add new assets found
4. Handle file format changes gracefully

## Troubleshooting

If you encounter issues:
1. Check your internet connection
2. Verify the board URLs are correct and accessible
3. Ensure you have write permissions in the script's directory
4. Check the console output for error messages
5. Make sure your virtualenv is activated (you should see `(venv)` in your terminal prompt)

## Requirements

- Python 3.6+
- requests library
- beautifulsoup4 library

## Limitations

- Only works with Getty Images boards
- Requires public board URLs
- Rate limited by Getty's API

## Deactivating the Virtual Environment

When you're done, you can deactivate the virtual environment:

```bash
deactivate
```