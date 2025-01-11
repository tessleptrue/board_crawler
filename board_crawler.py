import os
import json
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import logging
from typing import List, Dict, Optional, Set

class GettyBoardParser:
    """Parser for Getty Images board pages"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-platform': '"macOS"'
        }

    def _fetch_asset_list(self, board_id: str) -> List[Dict]:
        """Fetch the list of assets from the board"""
        url = f"https://www.gettyimages.com/collaboration/boards/{board_id}/asset_list"
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('assets', [])

    def _fetch_asset_metadata(self, asset_ids: List[str]) -> List[Dict]:
        """Fetch detailed metadata for assets"""
        # Join asset IDs with commas
        ids_param = ','.join(asset_ids)
        url = "https://www.gettyimages.com/collaboration/board_assets.json"
        params = {
            'asset_ids': ids_param
        }
        
        response = self.session.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def parse(self, board_url: str) -> List[Dict]:
        """Parse a Getty Images board and return asset data"""
        # Extract board ID from URL
        board_id = board_url.split('/')[-1]
        
        try:
            # First get the asset list
            assets = self._fetch_asset_list(board_id)
            if not assets:
                logging.warning(f"No assets found in board {board_id}")
                return []
            
            # Extract asset IDs
            asset_ids = [asset['uri'].replace('gi:', '') for asset in assets]
            
            # Create lookup for asset list data
            asset_list_lookup = {asset['uri'].replace('gi:', ''): asset for asset in assets}
            
            # Fetch detailed metadata for all assets
            metadata = self._fetch_asset_metadata(asset_ids)
            
            # Combine asset list data with metadata
            records = []
            for asset_data in metadata:
                asset_id = asset_data['id']
                asset_list_data = asset_list_lookup.get(asset_id, {})
                
                record = {
                    'board_id': board_id,
                    'asset_id': asset_id,
                    'added_by_id': asset_list_data.get('added_by_id', ''),
                    'added_date': asset_list_data.get('added_date', ''),
                    'title': asset_data.get('title', ''),
                    'caption': asset_data.get('caption', ''),
                    'date_created': asset_data.get('date_created', ''),
                    'date_submitted': asset_data.get('date_submitted', ''),
                    'artist': asset_data.get('artist', ''),
                    'collection_name': asset_data.get('collection', {}).get('name', ''),
                    'asset_family': asset_data.get('asset_family', ''),
                    'asset_type': asset_data.get('asset_type', ''),
                    'license_type': asset_data.get('license_type', ''),
                    'is_video': asset_data.get('is_video', False),
                    'release_info': asset_data.get('release', {}).get('text', ''),
                    'preview_url': asset_data.get('delivery_urls', {}).get('comp', ''),
                    'source_url': board_url
                }
                records.append(record)
            
            logging.info(f"Found {len(records)} assets in board {board_id}")
            return records
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data for board {board_id}: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error processing board {board_id}: {str(e)}")
            return []

class WebCrawler:
    def __init__(self, output_file: str = "board_data.csv"):
        """Initialize the web crawler."""
        # Set up logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.output_file = output_file
        self.existing_records = set()
        self.parser = GettyBoardParser()
        
        # Load existing records (will handle errors gracefully)
        self._load_existing_records()

    def _load_existing_records(self):
        """Load existing records to avoid duplicates."""
        try:
            with open(self.output_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check if we have the required columns
                if 'board_id' not in reader.fieldnames or 'asset_id' not in reader.fieldnames:
                    logging.warning("Existing CSV has different schema - creating new file")
                    # Rename the old file
                    os.rename(self.output_file, f"{self.output_file}.old")
                    return
                
                for row in reader:
                    # Create a unique identifier for each record
                    record_id = f"{row['board_id']}_{row['asset_id']}"
                    self.existing_records.add(record_id)
                logging.info(f"Loaded {len(self.existing_records)} existing records")
        except FileNotFoundError:
            logging.info("No existing records file found - will create new one")
        except Exception as e:
            logging.error(f"Error loading existing records: {str(e)}")
            # Rename problematic file instead of failing
            if os.path.exists(self.output_file):
                os.rename(self.output_file, f"{self.output_file}.error")
            logging.info("Renamed problematic file and will start fresh")

    def _save_records(self, records: List[Dict]):
        """Save new records to CSV file."""
        if not records:
            logging.info("No new records to save")
            return

        try:
            new_records = []
            for record in records:
                record_id = f"{record['board_id']}_{record['asset_id']}"
                if record_id not in self.existing_records:
                    new_records.append(record)
                    self.existing_records.add(record_id)

            if not new_records:
                logging.info("No new unique records found")
                return

            # If file doesn't exist, create it with headers
            file_exists = os.path.exists(self.output_file)
            mode = 'a' if file_exists else 'w'
            
            with open(self.output_file, mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=new_records[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)
                
            logging.info(f"Saved {len(new_records)} new records")
        except Exception as e:
            logging.error(f"Error saving records: {str(e)}")
            raise

    def crawl_boards(self, urls: List[str]):
        """Crawl multiple board URLs."""
        for url in urls:
            try:
                logging.info(f"Crawling board: {url}")
                records = self.parser.parse(url)
                self._save_records(records)
            except Exception as e:
                logging.error(f"Failed to crawl {url}: {str(e)}")
                continue

def main():
    # List of board URLs to crawl
    urls = [
        "https://www.gettyimages.com/collaboration/boards/IihIOXzjIke8Mc_He0lTMw",
        # Add more Getty Images board URLs here
    ]
    
    # Initialize and run crawler
    crawler = WebCrawler(output_file="board_data.csv")
    crawler.crawl_boards(urls)

if __name__ == "__main__":
    main()