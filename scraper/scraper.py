#!/usr/bin/env python3
"""
Web scraper for Once upon a Galaxy wiki cards
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse

class GalaxyWikiScraper:
    def __init__(self):
        self.base_url = "https://onceuponagalaxy.wiki.gg"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url):
        """Fetch page content with error handling"""
        try:
            response = self.session.get(url)
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
        cards = []
        
        # Look for card links in the category page
        # This will need to be adjusted based on the actual HTML structure
        card_links = soup.find_all('a', href=True)
        
        for link in card_links:
            href = link.get('href')
            if href and '/wiki/' in href and not href.startswith('http'):
                # This is likely a card page
                card_url = urljoin(self.base_url, href)
                card_data = self.scrape_card_page(card_url)
                if card_data:
                    cards.append(card_data)
                    print(f"Scraped: {card_data['name']}")
                    time.sleep(1)  # Be respectful to the server
        
        return cards
    
    def scrape_card_page(self, card_url):
        """Scrape individual card page to extract card data"""
        print(f"Scraping card page: {card_url}")
        
        content = self.get_page_content(card_url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract card name (usually in the page title or main heading)
        card_name = self.extract_card_name(soup)
        if not card_name:
            return None
        
        # Extract card description/effect text
        card_description = self.extract_card_description(soup)
        
        # Extract other card properties if available
        card_type = self.extract_card_type(soup)
        card_rarity = self.extract_card_rarity(soup)
        card_cost = self.extract_card_cost(soup)
        
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
        
        return card_data
    
    def extract_card_name(self, soup):
        """Extract card name from the page"""
        # Try to find the main heading (h1)
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Fallback to page title
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Remove common wiki suffixes
            if ' - Once upon a Galaxy Wiki' in title_text:
                return title_text.replace(' - Once upon a Galaxy Wiki', '').strip()
            return title_text
        
        return None
    
    def extract_card_description(self, soup):
        """Extract card description/effect text"""
        # Look for common patterns in card descriptions
        # This will need to be customized based on the actual wiki structure
        
        # Try to find description in infobox or main content
        infobox = soup.find('table', class_='infobox')
        if infobox:
            # Look for description in infobox
            desc_row = infobox.find('td', string=lambda text: text and 'description' in text.lower())
            if desc_row and desc_row.find_next_sibling('td'):
                return desc_row.find_next_sibling('td').get_text().strip()
        
        # Look for description in main content area
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            # Find paragraphs that might contain card effects
            paragraphs = main_content.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Likely a description
                    return text
        
        return None
    
    def extract_card_type(self, soup):
        """Extract card type if available"""
        # Look for type information in infobox or content
        infobox = soup.find('table', class_='infobox')
        if infobox:
            type_row = infobox.find('td', string=lambda text: text and 'type' in text.lower())
            if type_row and type_row.find_next_sibling('td'):
                return type_row.find_next_sibling('td').get_text().strip()
        return None
    
    def extract_card_rarity(self, soup):
        """Extract card rarity if available"""
        # Look for rarity information
        infobox = soup.find('table', class_='infobox')
        if infobox:
            rarity_row = infobox.find('td', string=lambda text: text and 'rarity' in text.lower())
            if rarity_row and rarity_row.find_next_sibling('td'):
                return rarity_row.find_next_sibling('td').get_text().strip()
        return None
    
    def extract_card_cost(self, soup):
        """Extract card cost if available"""
        # Look for cost information
        infobox = soup.find('table', class_='infobox')
        if infobox:
            cost_row = infobox.find('td', string=lambda text: text and 'cost' in text.lower())
            if cost_row and cost_row.find_next_sibling('td'):
                cost_text = cost_row.find_next_sibling('td').get_text().strip()
                try:
                    return int(cost_text)
                except ValueError:
                    return cost_text
        return None
    
    def save_cards_to_json(self, cards, output_dir="cards"):
        """Save scraped cards to individual JSON files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for card in cards:
            if card and card.get('name'):
                # Create filename from card name
                filename = card['name'].lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')
                filename = ''.join(c for c in filename if c.isalnum() or c == '-')
                filename = f"{output_dir}/{filename}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(card, f, indent=2, ensure_ascii=False)
                
                print(f"Saved: {filename}")
    
    def run(self, category_url):
        """Main method to run the scraper"""
        print("Starting Once upon a Galaxy wiki scraper...")
        
        # Scrape the treasures category
        cards = self.scrape_treasures_category(category_url)
        
        print(f"\nScraped {len(cards)} cards")
        
        # Save cards to JSON files
        self.save_cards_to_json(cards)
        
        print("Scraping completed!")

if __name__ == "__main__":
    scraper = GalaxyWikiScraper()
    
    # URL for the treasures category
    treasures_url = "https://onceuponagalaxy.wiki.gg/wiki/Category:Treasures"
    
    # Run the scraper
    scraper.run(treasures_url)
