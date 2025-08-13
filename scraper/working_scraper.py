#!/usr/bin/env python3
"""
Working scraper for Once upon a Galaxy wiki using curl user agent
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urljoin

class WorkingGalaxyScraper:
    def __init__(self):
        self.base_url = "https://onceuponagalaxy.wiki.gg"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'curl/7.68.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def get_page_content(self, url):
        """Fetch page content with error handling"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def scrape_treasures_category(self, category_url):
        """Scrape the treasures category page to get all treasure cards"""
        print(f"Scraping treasures category: {category_url}")
        
        content = self.get_page_content(category_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Save the raw HTML for inspection
        with open('debug_treasures_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Saved debug HTML to debug_treasures_page.html")
        
        # Look for the main content area
        main_content = soup.find('div', id='mw-content-text')
        if not main_content:
            print("Could not find main content area")
            return []
        
        # Look for links to individual card pages
        card_links = []
        
        # Try different approaches to find card links
        # 1. Look for links in the category listing
        links = main_content.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Filter for likely card pages (not templates or categories)
            if (href.startswith('/wiki/') and 
                not href.startswith('/wiki/Template:') and
                not href.startswith('/wiki/Category:') and
                not href.startswith('/wiki/User:') and
                not href.startswith('/wiki/Talk:') and
                not href.startswith('/wiki/File:') and
                not href.startswith('/wiki/Help:') and
                not href.startswith('/wiki/Special:') and
                text and len(text) > 1 and
                not text.startswith('Template:')):
                
                card_links.append({
                    'url': urljoin(self.base_url, href),
                    'name': text,
                    'href': href
                })
        
        print(f"Found {len(card_links)} potential card links")
        
        # Remove duplicates based on URL
        unique_links = []
        seen_urls = set()
        for link in card_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"After deduplication: {len(unique_links)} unique card links")
        
        # Scrape each card page
        cards = []
        for i, link in enumerate(unique_links[:10]):  # Limit to first 10 for testing
            print(f"\nScraping card {i+1}/{min(10, len(unique_links))}: {link['name']}")
            card_data = self.scrape_card_page(link['url'], link['name'])
            if card_data:
                cards.append(card_data)
                print(f"Successfully scraped: {card_data['name']}")
            else:
                print(f"Failed to scrape: {link['name']}")
            
            time.sleep(2)  # Be respectful to the server
        
        return cards
    
    def scrape_card_page(self, card_url, expected_name):
        """Scrape individual card page to extract card data"""
        content = self.get_page_content(card_url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract card name
        card_name = self.extract_card_name(soup, expected_name)
        if not card_name:
            return None
        
        # Extract card description/effect text
        card_description = self.extract_card_description(soup)
        
        # Extract other card properties if available
        card_type = self.extract_card_type(soup)
        card_rarity = self.extract_card_rarity(soup)
        card_cost = self.extract_card_cost(soup)
        card_images = self.extract_card_images(soup)
        
        card_data = {
            "name": card_name,
            "description": card_description or "No description available"
        }
        
        # Add optional fields if found
        if card_type:
            card_data["type"] = card_type
        if card_rarity:
            card_data["rarity"] = card_rarity
        if card_cost:
            card_data["cost"] = card_cost
        if card_images:
            card_data["images"] = card_images
        
        return card_data
    
    def extract_card_name(self, soup, expected_name):
        """Extract card name from the page"""
        # Try to find the main heading (h1)
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text().strip()
            if name and name != expected_name:
                print(f"  Name mismatch: expected '{expected_name}', got '{name}'")
            return name or expected_name
        
        # Fallback to page title
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Remove common wiki suffixes
            if ' - Once Upon a Galaxy Wiki' in title_text:
                return title_text.replace(' - Once Upon a Galaxy Wiki', '').strip()
            return title_text
        
        return expected_name
    
    def extract_card_description(self, soup):
        """Extract card description/effect text"""
        # Look for description in the druid-infobox (card attributes)
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Look for the ability section
            ability_row = infobox.find('div', class_='druid-row-ability')
            if ability_row:
                ability_data = ability_row.find('div', class_='druid-data-ability')
                if ability_data:
                    # Get the text content, but clean up links
                    ability_text = ability_data.get_text().strip()
                    if ability_text:
                        return ability_text
            
            # If no ability found, look for any other descriptive text
            all_data = infobox.find_all('div', class_='druid-data')
            for data in all_data:
                text = data.get_text().strip()
                if text and len(text) > 10 and not text.startswith('http'):
                    return text
        
        # Fallback to main content area
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            # Find paragraphs that might contain card effects
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20 and not text.startswith('This page was last edited'):
                    return text
        
        return None
    
    def extract_card_type(self, soup):
        """Extract card type if available"""
        # Look for type information in druid-infobox
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Look for type/class information
            type_row = infobox.find('div', class_='druid-row-type')
            if type_row:
                type_data = type_row.find('div', class_='druid-data-type')
                if type_data:
                    return type_data.get_text().strip()
            
            # Check if it's a treasure (from the page structure)
            if infobox.find('div', class_='druid-section-attributes'):
                return 'treasure'
        
        return None
    
    def extract_card_rarity(self, soup):
        """Extract card rarity if available"""
        # Look for rarity information in druid-infobox
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            rarity_row = infobox.find('div', class_='druid-row-rarity')
            if rarity_row:
                rarity_data = rarity_row.find('div', class_='druid-data-rarity')
                if rarity_data:
                    # Get the text content, but clean up links
                    rarity_text = rarity_data.get_text().strip()
                    if rarity_text:
                        return rarity_text.lower()
        
        return None
    
    def extract_card_cost(self, soup):
        """Extract card cost if available"""
        # Look for cost information in content
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            text = main_content.get_text()
            # Look for cost patterns like "Cost: 3" or "3 cost"
            cost_match = re.search(r'cost[:\s]*(\d+)', text.lower())
            if cost_match:
                try:
                    return int(cost_match.group(1))
                except ValueError:
                    pass
        return None
    
    def extract_card_images(self, soup):
        """Extract art and card images from the page"""
        images = []
        
        # Method 1: Look for Open Graph images (most reliable)
        og_images = soup.find_all('meta', property='og:image')
        for og_img in og_images:
            url = og_img.get('content')
            if url and url.startswith('http'):
                # Determine image type based on URL
                if 'thumb' in url:
                    # This is a thumbnail, get the original
                    # Fix: properly reconstruct the original URL
                    parts = url.split('/')
                    if 'thumb' in parts:
                        thumb_index = parts.index('thumb')
                        # Remove 'thumb' and the size part, but keep the directory structure
                        original_parts = parts[:thumb_index] + parts[thumb_index+2:]
                        original_url = '/'.join(original_parts)
                        
                        images.append({
                            'type': 'art',
                            'url': original_url
                        })
                else:
                    images.append({
                        'type': 'art',
                        'url': url
                    })
        
        # Method 2: Look for images in druid-infobox (most specific)
        infobox = soup.find('div', class_='druid-infobox')
        if infobox:
            # Find the main images section
            main_images = infobox.find('div', class_='druid-main-images')
            if main_images:
                # Look for image files (not tabs)
                image_files = main_images.find_all('div', class_='druid-main-images-file')
                
                for img_file in image_files:
                    # Get the tab key to determine type
                    tab_key = img_file.get('data-druid-tab-key', 'unknown')
                    
                    # Find the img tag within this file div
                    img_tag = img_file.find('img', src=True)
                    if img_tag:
                        src = img_tag.get('src')
                        alt = img_tag.get('alt', '')
                        
                        if src and not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Get the original image URL (not thumbnail)
                        if 'thumb' in src:
                            parts = src.split('/')
                            if 'thumb' in parts:
                                thumb_index = parts.index('thumb')
                                # Remove 'thumb' and the size part, but keep the directory structure
                                original_parts = parts[:thumb_index] + parts[thumb_index+2:]
                                original_url = '/'.join(original_parts)
                            else:
                                original_url = src
                        else:
                            original_url = src
                        
                        # Determine image type based on tab key
                        img_type = 'art' if tab_key == 'Art' else 'card' if tab_key == 'Card' else 'unknown'
                        
                        images.append({
                            'type': img_type,
                            'url': original_url
                        })
        
        # Remove duplicates based on URL
        unique_images = []
        seen_urls = set()
        for img in images:
            if img['url'] not in seen_urls:
                unique_images.append(img)
                seen_urls.add(img['url'])
        
        return unique_images
    
    def save_cards_to_json(self, cards, output_dir="cards/treasures"):
        """Save scraped cards to individual JSON files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for card in cards:
            if card and card.get('name'):
                # Create filename from card name
                filename = card['name'].lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')
                filename = re.sub(r'[^a-z0-9\-]', '', filename)
                filename = f"{output_dir}/{filename}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(card, f, indent=2, ensure_ascii=False)
                
                print(f"Saved: {filename}")
    
    def run(self, category_url):
        """Main method to run the scraper"""
        print("Starting Working Once upon a Galaxy wiki scraper...")
        
        # Scrape the treasures category
        cards = self.scrape_treasures_category(category_url)
        
        print(f"\nScraped {len(cards)} cards")
        
        # Save cards to JSON files
        self.save_cards_to_json(cards)
        
        print("Scraping completed!")

if __name__ == "__main__":
    scraper = WorkingGalaxyScraper()
    
    # URL for the treasures category
    treasures_url = "https://onceuponagalaxy.wiki.gg/wiki/Category:Treasures"
    
    # Run the scraper
    scraper.run(treasures_url)
