import os
import json
import csv
import subprocess
from datetime import datetime
import logging
from typing import List, Dict

class GettyBoardParser:
    def __init__(self):
        # Verify curl is available
        try:
            subprocess.run(['curl', '--version'], capture_output=True)
        except FileNotFoundError:
            raise RuntimeError("curl is not installed or not available in PATH")

    def _fetch_assets(self, board_id: str) -> List[Dict]:
        """Fetch the list of assets from the board using curl"""
        url = f"https://www.gettyimages.com/collaboration/boards/{board_id}/asset_list"
        logging.info(f"Fetching assets URL: {url}")
        
        try:
            # Run curl command and capture output
            result = subprocess.run(['curl', url], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"curl failed with return code {result.returncode}: {result.stderr}")
            
            return json.loads(result.stdout).get('assets', [])
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from curl output: {str(e)}")
            logging.error(f"Curl output: {result.stdout[:1000]}")  # First 1000 chars
            raise
        except Exception as e:
            logging.error(f"Curl command failed: {str(e)}")
            raise

    def _fetch_metadata(self, asset_ids: List[str]) -> List[Dict]:
        """Fetch detailed metadata for assets using curl"""
        url = "https://www.gettyimages.com/collaboration/board_assets.json"
        asset_ids_param = ','.join(asset_ids)
        full_url = f"{url}?asset_ids={asset_ids_param}"
        logging.info(f"Fetching metadata URL: {full_url}")
        
        try:
            result = subprocess.run(['curl', full_url], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"curl failed with return code {result.returncode}: {result.stderr}")
            
            return json.loads(result.stdout)
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from curl output: {str(e)}")
            logging.error(f"Curl output: {result.stdout[:1000]}")
            raise
        except Exception as e:
            logging.error(f"Curl command failed: {str(e)}")
            raise

    def parse(self, board_url: str) -> List[Dict]:
        board_id = board_url.split('/')[-1]
        
        try:
            logging.info(f"Fetching assets for board ID: {board_id}")
            assets = self._fetch_assets(board_id)
            
            if not assets:
                logging.info("No assets found in response")
                return []
            
            asset_ids = [asset['uri'].replace('gi:', '') for asset in assets]
            asset_list_lookup = {asset['uri'].replace('gi:', ''): asset for asset in assets}
            metadata = self._fetch_metadata(asset_ids)
            
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
            
            return records
            
        except Exception as e:
            logging.error(f"Error processing board {board_id}: {str(e)}")
            raise

class WebCrawler:
    def __init__(self, output_file: str = "board_data.csv", exclude_columns: List[str] = None):
        """
        Initialize the web crawler.
        
        Args:
            output_file (str): Path to the CSV output file
            exclude_columns (List[str]): List of column names to exclude from the output
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.output_file = output_file
        self.exclude_columns = exclude_columns or []
        self.existing_records = set()
        self.parser = GettyBoardParser()
        self._load_existing_records()
        
        # Log excluded columns
        if self.exclude_columns:
            logging.info(f"The following columns will be excluded: {', '.join(self.exclude_columns)}")

    def _filter_record(self, record: Dict) -> Dict:
        """Remove excluded columns from a record."""
        return {k: v for k, v in record.items() if k not in self.exclude_columns}

    def _load_existing_records(self):
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
        if not records:
            logging.info("No new records to save")
            return

        try:
            # Filter excluded columns from records
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
        for url in urls:
            try:
                logging.info(f"Processing board: {url}")
                records = self.parser.parse(url)
                self._save_records(records)
                logging.info(f"Successfully processed {len(records)} records")
            except Exception as e:
                logging.error(f"Failed to process {url}: {str(e)}")

def main():
    # Example: exclude certain columns
    exclude_columns = [
        'release_info',       # Hide release information
        'added_by_id',        # Hide user IDs
        'license_type',       # Hide license information 
        'source_url'        # Hide source URLs
    ]
    
    urls = [
        "https://www.gettyimages.com/collaboration/boards/IihIOXzjIke8Mc_He0lTMw",
    ]
    
    crawler = WebCrawler(
        output_file="board_data.csv",
        exclude_columns=exclude_columns
    )
    crawler.crawl_boards(urls)

if __name__ == "__main__":
    main()

