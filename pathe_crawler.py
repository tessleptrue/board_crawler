import os
import csv 
import logging
from typing import List, Dict
import re
from bs4 import BeautifulSoup
import requests
from datetime import datetime

class PatheBoardParser:
    """Parser for British Pathé lightbox pages"""
    
    def _extract_token(self, url: str) -> str:
        """Extract the token from the British Pathe URL"""
        match = re.search(r'st=([^&]+)', url)
        if not match:
            raise ValueError("Could not extract token from URL")
        return match.group(1)

    def _fetch_page(self, url: str) -> str:
        """Fetch a page and return its HTML content"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"Error fetching URL {url}: {str(e)}")
            raise

    def _fetch_assets(self, lightbox_token: str) -> List[Dict]:
        """Fetch assets from British Pathe lightbox"""
        url = f"https://www.britishpathe.com/lightbox/?st={lightbox_token}"
        logging.info(f"Fetching assets from British Pathe URL: {url}")

        try:
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            assets = []
            # Look for video containers in the lightbox
            for asset in soup.select('.lightboxAsset'):
                asset_id = asset.get('data-id')
                lightbox_item_id = asset.get('data-lightbox-id')
                
                if asset_id:
                    # Extract thumbnail image URL
                    img_elem = asset.select_one('img')
                    preview_url = img_elem['src'] if img_elem else ''
                    
                    # Extract video preview URL if available
                    video_elem = asset.select_one('source')
                    video_url = video_elem['src'] if video_elem else ''
                    
                    asset_data = {
                        'asset_id': asset_id,
                        'lightbox_item_id': lightbox_item_id,
                        'preview_url': preview_url,
                        'video_url': video_url
                    }
                    assets.append(asset_data)
            
            return assets

        except Exception as e:
            logging.error(f"Error fetching British Pathe assets: {str(e)}")
            raise

    def _fetch_metadata(self, asset_id: str) -> Dict:
        """Fetch metadata for a single British Pathe asset"""
        url = f"https://www.britishpathe.com/asset/{asset_id}"
        logging.info(f"Fetching metadata for asset {asset_id}")
        
        try:
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract available metadata fields
            metadata = {}
            
            # Get title if available
            title_elem = soup.select_one('.assetName')
            if title_elem:
                metadata['title'] = title_elem.text.strip()
            
            # Get description/caption if available
            desc_elem = soup.select_one('.desc')
            if desc_elem:
                metadata['description'] = desc_elem.text.strip()
            
            # Get date if available
            date_elem = soup.select_one('.date')
            if date_elem:
                metadata['date'] = date_elem.text.strip()
            
            # Get any keywords/tags
            keywords = []
            for keyword in soup.select('.keywordItem'):
                kw = keyword.text.strip()
                if kw:
                    keywords.append(kw)
            if keywords:
                metadata['keywords'] = '; '.join(keywords)
            
            metadata['source_url'] = url
            return metadata
            
        except Exception as e:
            logging.error(f"Error fetching metadata for asset {asset_id}: {str(e)}")
            return {}

    def parse(self, board_url: str) -> List[Dict]:
        """Parse a British Pathe lightbox URL and extract all asset information"""
        try:
            token = self._extract_token(board_url)
            assets = self._fetch_assets(token)
            
            records = []
            for asset in assets:
                metadata = self._fetch_metadata(asset['asset_id'])
                
                record = {
                    'board_id': token,
                    'asset_id': asset['asset_id'],
                    'lightbox_item_id': asset.get('lightbox_item_id', ''),
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'date': metadata.get('date', ''),
                    'keywords': metadata.get('keywords', ''),
                    'thumbnail_url': asset['preview_url'],
                    'video_url': asset.get('video_url', ''),
                    'source_url': metadata.get('source_url', ''),
                    'crawl_date': datetime.now().isoformat()
                }
                records.append(record)
                
            return records
            
        except Exception as e:
            logging.error(f"Error processing British Pathe board: {str(e)}")
            raise

class PatheCrawler:
    """Crawler for saving British Pathe lightbox data"""
    
    def __init__(self, output_file: str = "pathe_data.csv", exclude_columns: List[str] = None):
        """
        Initialize the crawler
        
        Args:
            output_file: Path to CSV output file
            exclude_columns: List of column names to exclude from output
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.output_file = output_file
        self.exclude_columns = exclude_columns or []
        self.existing_records = set()
        self.parser = PatheBoardParser()
        self._load_existing_records()
        
        if self.exclude_columns:
            logging.info(f"Excluding columns: {', '.join(self.exclude_columns)}")

    def _filter_record(self, record: Dict) -> Dict:
        """Remove excluded columns from a record"""
        return {k: v for k, v in record.items() if k not in self.exclude_columns}

    def _load_existing_records(self):
        """Load existing records to avoid duplicates"""
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        record_id = f"{row['board_id']}_{row['asset_id']}"
                        self.existing_records.add(record_id)
                    logging.info(f"Loaded {len(self.existing_records)} existing records")
            else:
                logging.info("No existing records file found - will create new one")
        except Exception as e:
            logging.error(f"Error loading existing records: {str(e)}")
            if os.path.exists(self.output_file):
                os.rename(self.output_file, f"{self.output_file}.error")
            logging.info("Renamed problematic file and will start fresh")

    def _save_records(self, records: List[Dict]):
        """Save new records to CSV file"""
        if not records:
            logging.info("No new records to save")
            return

        try:
            filtered_records = [self._filter_record(record) for record in records]
            
            new_records = []
            for record in filtered_records:
                record_id = f"{record['board_id']}_{record['asset_id']}"
                if record_id not in self.existing_records:
                    new_records.append(record)
                    self.existing_records.add(record_id)

            if not new_records:
                logging.info("No new unique records found")
                return

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
        """Crawl a list of British Pathe lightbox URLs"""
        for url in urls:
            try:
                logging.info(f"Processing board: {url}")
                records = self.parser.parse(url)
                self._save_records(records)
                logging.info(f"Successfully processed {len(records)} records")
            except Exception as e:
                logging.error(f"Failed to process {url}: {str(e)}")

def main():
    # Example usage
    exclude_columns = [
        'source_url',         # Hide source URLs
        'lightbox_item_id'    # Hide internal IDs
    ]
    
    urls = [
        "https://www.britishpathe.com/lightbox/?st=5ef64e21f363bcce67d98ba5439a78ebbec82613&target=same"
    ]
    
    crawler = PatheCrawler(
        output_file="pathe_data.csv",
        exclude_columns=exclude_columns
    )
    crawler.crawl_boards(urls)

if __name__ == "__main__":
    main()