#!/usr/bin/env python3
"""
Image scraper for Once Upon a Galaxy cards.
Downloads PNG images, converts to JPG, and updates JSON files with local paths.
"""

import json
import os
import requests
from PIL import Image
import argparse
from pathlib import Path
import time

class ImageScraper:
    def __init__(self, output_dir="images"):
        self.output_dir = Path(output_dir)
        self.original_dir = self.output_dir / "original"
        self.converted_dir = self.output_dir / "converted"
        
        # Create directories
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.converted_dir.mkdir(parents=True, exist_ok=True)
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, url, filename):
        """Download image from URL and save to original directory."""
        try:
            print(f"Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = self.original_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Saved: {filepath}")
            return filepath
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None
    
    def convert_to_webp(self, png_path, quality=85):
        """Convert PNG to WebP with specified quality, preserving transparency."""
        try:
            with Image.open(png_path) as img:
                # Convert to RGBA if necessary to preserve transparency
                if img.mode == 'P':
                    img = img.convert('RGBA')
                elif img.mode not in ('RGBA', 'LA'):
                    img = img.convert('RGBA')
                
                # Generate WebP filename
                webp_filename = png_path.stem + '.webp'
                webp_path = self.converted_dir / webp_filename
                
                # Save as WebP with transparency support
                img.save(webp_path, 'WEBP', quality=quality, lossless=False)
                print(f"Converted: {webp_path}")
                return webp_path
        except Exception as e:
            print(f"Failed to convert {png_path}: {e}")
            return None
    
    def process_character_images(self, card_data, card_name):
        """Process images for character cards - only Bronze and Gold."""
        if not card_data.get('images'):
            return []
        
        processed_images = []
        
        for img_data in card_data['images']:
            url = img_data.get('url', '')
            img_type = img_data.get('type', 'unknown')
            
            # For characters, only process Bronze and Gold images
            if 'Bronze' in url or 'Gold' in url:
                # Generate filename
                safe_name = card_name.lower().replace(' ', '-').replace("'", '').replace('"', '')
                filename = f"{safe_name}_{img_type}_{len(processed_images)}.png"
                
                # Download PNG
                png_path = self.download_image(url, filename)
                if png_path:
                    # Convert to WebP
                    webp_path = self.convert_to_webp(png_path)
                    if webp_path:
                        # Update image data
                        processed_img = {
                            'url': url,  # Keep original URL
                            'type': img_type,
                            'original': str(png_path.relative_to(self.output_dir)),
                            'converted': str(webp_path.relative_to(self.output_dir))
                        }
                        processed_images.append(processed_img)
                        
                        # Small delay to be respectful
                        time.sleep(0.5)
        
        return processed_images
    
    def process_other_images(self, card_data, card_name):
        """Process images for non-character cards - prefer 'card' type, fallback to first available."""
        if not card_data.get('images'):
            return []
        
        processed_images = []
        
        # First, try to find a 'card' type image
        card_image = None
        for img_data in card_data['images']:
            if img_data.get('type') == 'card':
                card_image = img_data
                break
        
        # If no 'card' type found, use the first available image
        if not card_image:
            card_image = card_data['images'][0]
        
        url = card_image.get('url', '')
        img_type = card_image.get('type', 'unknown')
        
        # Generate filename
        safe_name = card_name.lower().replace(' ', '-').replace("'", '').replace('"', '')
        filename = f"{safe_name}_{img_type}_{len(processed_images)}.png"
        
        # Download PNG
        png_path = self.download_image(url, filename)
        if png_path:
            # Convert to WebP
            webp_path = self.convert_to_webp(png_path)
            if webp_path:
                # Update image data
                processed_img = {
                    'url': url,  # Keep original URL
                    'type': img_type,
                    'original': str(png_path.relative_to(self.output_dir)),
                    'converted': str(webp_path.relative_to(self.output_dir))
                }
                processed_images.append(processed_img)
                
                # Small delay to be respectful
                time.sleep(0.5)
        
        return processed_images
    
    def process_card_file(self, json_path):
        """Process a single card JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            card_name = card_data.get('name', 'Unknown')
            card_type = card_data.get('type', 'unknown')
            
            print(f"\nProcessing: {card_name} ({card_type})")
            
            if card_type == 'characters':
                processed_images = self.process_character_images(card_data, card_name)
            else:
                processed_images = self.process_other_images(card_data, card_name)
            
            if processed_images:
                # Update the card data with local paths
                card_data['images'] = processed_images
                
                # Save updated JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(card_data, f, indent=2, ensure_ascii=False)
                
                print(f"Updated {json_path} with {len(processed_images)} local images")
            else:
                print(f"No images processed for {card_name}")
                
        except Exception as e:
            print(f"Error processing {json_path}: {e}")
    
    def run(self, card_type=None, specific_card=None):
        """Run the image scraper."""
        cards_dir = Path("cards")
        
        if not cards_dir.exists():
            print("Cards directory not found!")
            return
        
        if specific_card:
            # Process specific card
            card_path = cards_dir / card_type / f"{specific_card}.json"
            if card_path.exists():
                self.process_card_file(card_path)
            else:
                print(f"Card file not found: {card_path}")
        else:
            # Process all cards of specified type
            type_dir = cards_dir / card_type
            if not type_dir.exists():
                print(f"Type directory not found: {type_dir}")
                return
            
            json_files = list(type_dir.glob("*.json"))
            print(f"Found {len(json_files)} {card_type} cards")
            
            for json_file in json_files:
                self.process_card_file(json_file)

def main():
    parser = argparse.ArgumentParser(description="Scrape and convert card images")
    parser.add_argument("--type", choices=["characters", "treasures", "spells"], 
                       help="Card type to process")
    parser.add_argument("--card", help="Specific card name to process (without .json)")
    parser.add_argument("--output", default="images", help="Output directory for images")
    
    args = parser.parse_args()
    
    if not args.type:
        print("Please specify --type (characters, treasures, or spells)")
        return
    
    scraper = ImageScraper(args.output)
    scraper.run(args.type, args.card)

if __name__ == "__main__":
    main()
