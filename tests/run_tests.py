#!/usr/bin/env python3
"""
Test runner for card scraper tests
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scraper'))
from test_card_scraper import TestCardScraper

if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCardScraper)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    sys.exit(0 if result.wasSuccessful() else 1)
