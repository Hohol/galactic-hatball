#!/usr/bin/env python3
"""
Unit tests for card_scraper.py
Tests the ability extraction logic and other key functionality
"""

import unittest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import sys
import os

# Add the scraper directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scraper'))
from card_scraper import WorkingGalaxyScraper


class TestCardScraper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = WorkingGalaxyScraper()
        
    def create_mock_soup(self, html_content):
        """Helper method to create BeautifulSoup object from HTML string"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def test_extract_card_abilities_primary_only(self):
        """Test extraction of primary ability only"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability_type">
                <div class="druid-data-ability_type">Ranged</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0]["type"], "Ranged")
        self.assertIsNone(abilities[0]["description"])
        self.assertIsNone(abilities[0]["gold_description"])
    
    def test_extract_card_abilities_primary_with_description(self):
        """Test extraction of primary ability with description"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability_type">
                <div class="druid-data-ability_type">Hunt</div>
            </div>
            <div class="druid-row-ability_description">
                <div class="druid-data-ability_description">+6/+6</div>
            </div>
            <div class="druid-row-ability_description_gold">
                <div class="druid-data-ability_description_gold">+12/+12</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0]["type"], "Hunt")
        self.assertEqual(abilities[0]["description"], "+6/+6")
        self.assertEqual(abilities[0]["gold_description"], "+12/+12")
    
    def test_extract_card_abilities_primary_and_secondary(self):
        """Test extraction of primary and secondary abilities"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability_type">
                <div class="druid-data-ability_type">Treasure Hoard 2</div>
            </div>
            <div class="druid-row-ability_2_description">
                <div class="druid-data-ability_2_description">Deal (X) damage to an enemy.</div>
            </div>
            <div class="druid-row-ability_2_description_gold">
                <div class="druid-data-ability_2_description_gold">Deal (2X) damage to an enemy.</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 2)
        
        # Primary ability
        self.assertEqual(abilities[0]["type"], "Treasure Hoard 2")
        self.assertIsNone(abilities[0]["description"])
        self.assertIsNone(abilities[0]["gold_description"])
        
        # Secondary ability
        self.assertIsNone(abilities[1]["type"])
        self.assertEqual(abilities[1]["description"], "Deal (X) damage to an enemy.")
        self.assertEqual(abilities[1]["gold_description"], "Deal (2X) damage to an enemy.")
    
    def test_extract_card_abilities_three_abilities(self):
        """Test extraction of three abilities (primary, secondary, tertiary)"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability_type">
                <div class="druid-data-ability_type">Primary</div>
            </div>
            <div class="druid-row-ability_2_description">
                <div class="druid-data-ability_2_description">Secondary effect</div>
            </div>
            <div class="druid-row-ability_3_type">
                <div class="druid-data-ability_3_type">Tertiary</div>
            </div>
            <div class="druid-row-ability_3_description">
                <div class="druid-data-ability_3_description">Tertiary effect</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 3)
        
        # Primary ability
        self.assertEqual(abilities[0]["type"], "Primary")
        self.assertIsNone(abilities[0]["description"])
        self.assertIsNone(abilities[0]["gold_description"])
        
        # Secondary ability
        self.assertIsNone(abilities[1]["type"])
        self.assertEqual(abilities[1]["description"], "Secondary effect")
        self.assertIsNone(abilities[1]["gold_description"])
        
        # Tertiary ability
        self.assertEqual(abilities[2]["type"], "Tertiary")
        self.assertEqual(abilities[2]["description"], "Tertiary effect")
        self.assertIsNone(abilities[2]["gold_description"])
    
    def test_extract_card_abilities_empty_infobox(self):
        """Test extraction when no infobox is present"""
        html = '<div>No infobox here</div>'
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 0)
    
    def test_extract_card_abilities_no_abilities(self):
        """Test extraction when no abilities are present"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-rarity">
                <div class="druid-data-rarity">Common</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        abilities = self.scraper.extract_card_abilities(soup)
        
        self.assertEqual(len(abilities), 0)
    
    def test_extract_card_traits(self):
        """Test extraction of card traits"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-traits">
                <div class="druid-data-traits">
                    <ul>
                        <li><a href="/wiki/Dragon">Dragon</a></li>
                        <li><a href="/wiki/Celestial">Celestial</a></li>
                    </ul>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        traits = self.scraper.extract_card_traits(soup)
        
        self.assertEqual(traits, ["Dragon", "Celestial"])
    
    def test_extract_card_attack_health(self):
        """Test extraction of attack and health values"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-attack">
                <div class="druid-data-attack">25</div>
            </div>
            <div class="druid-row-health">
                <div class="druid-data-health">30</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        attack = self.scraper.extract_card_attack(soup)
        health = self.scraper.extract_card_health(soup)
        
        self.assertEqual(attack, 25)
        self.assertEqual(health, 30)
    
    def test_extract_card_rarity(self):
        """Test extraction of card rarity"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-rarity">
                <div class="druid-data-rarity">
                    <a href="/wiki/Rarity#Secret_Rare">Secret Rare</a>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        rarity = self.scraper.extract_card_rarity(soup)
        
        self.assertEqual(rarity, "secret rare")
    
    def test_extract_card_deck_type(self):
        """Test extraction of deck type"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-deck_type">
                <div class="druid-data-deck_type">
                    <a href="/wiki/Shared">Shared</a>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        deck_type = self.scraper.extract_card_deck_type(soup)
        
        self.assertEqual(deck_type, "Shared")
    
    def test_extract_card_images(self):
        """Test extraction of card images"""
        html = '''
        <meta property="og:image" content="https://example.com/image.png" />
        '''
        soup = self.create_mock_soup(html)
        images = self.scraper.extract_card_images(soup)
        
        self.assertGreater(len(images), 0)
        self.assertIn('type', images[0])
        self.assertIn('url', images[0])

    def test_extract_treasure_description(self):
        """Test extraction of treasure description from ability field"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability">
                <div class="druid-data-ability">Your first slot has +1000 Attack.</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        description = self.scraper.extract_card_description(soup)
        
        self.assertEqual(description, "Your first slot has +1000 Attack.")
    
    def test_extract_treasure_description_fallback(self):
        """Test extraction of treasure description from main content when not in infobox"""
        html = '''
        <div id="mw-content-text">
            <p>This is a powerful sword that grants +1000 Attack to your first slot.</p>
        </div>
        '''
        soup = self.create_mock_soup(html)
        description = self.scraper.extract_card_description(soup)
        
        self.assertEqual(description, "This is a powerful sword that grants +1000 Attack to your first slot.")
    
    def test_extract_treasure_description_excludes_traits(self):
        """Test that treasure description extraction excludes trait-like text"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-traits">
                <div class="druid-data-traits">
                    <a href="/wiki/Weapon">Weapon</a>
                </div>
            </div>
            <div class="druid-row-ability">
                <div class="druid-data-ability">Your first slot has +1000 Attack.</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        description = self.scraper.extract_card_description(soup)
        
        # Should get the description, not the trait
        self.assertEqual(description, "Your first slot has +1000 Attack.")
    
    def test_extract_treasure_rarity(self):
        """Test extraction of treasure rarity"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-rarity">
                <div class="druid-data-rarity">
                    <a href="/wiki/Rarity#Secret_Rare">Secret Rare</a>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        rarity = self.scraper.extract_card_rarity(soup)
        
        self.assertEqual(rarity, "secret rare")
    
    def test_extract_spell_description(self):
        """Test extraction of spell description from ability field"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-ability">
                <div class="druid-data-ability">Deal 3 damage to target creature.</div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        description = self.scraper.extract_card_description(soup)
        
        self.assertEqual(description, "Deal 3 damage to target creature.")
    
    def test_extract_spell_rarity(self):
        """Test extraction of spell rarity"""
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-rarity">
                <div class="druid-data-rarity">
                    <a href="/wiki/Rarity#Common">Common</a>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        rarity = self.scraper.extract_card_rarity(soup)
        
        self.assertEqual(rarity, "common")
    
    def test_extract_card_type_from_category(self):
        """Test that card type is correctly set from category name"""
        # This tests the scrape_card_page method indirectly
        # We'll test the type assignment logic
        html = '''
        <div class="druid-infobox">
            <div class="druid-row-rarity">
                <div class="druid-data-rarity">
                    <a href="/wiki/Rarity#Rare">Rare</a>
                </div>
            </div>
        </div>
        '''
        soup = self.create_mock_soup(html)
        
        # Test that the scraper correctly assigns type from category
        # We'll just verify the method exists and can be called
        self.assertTrue(hasattr(self.scraper, 'scrape_card_page'))
        
        # Test that rarity extraction works for treasures and spells
        rarity = self.scraper.extract_card_rarity(soup)
        self.assertEqual(rarity, "rare")


if __name__ == '__main__':
    unittest.main()
