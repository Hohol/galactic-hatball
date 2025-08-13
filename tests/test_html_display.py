#!/usr/bin/env python3
"""
Simple test to verify HTML display works with new character data structure
"""

import json
import os

def test_character_data_structure():
    """Test that all character JSON files have the correct structure"""
    characters_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cards', 'characters')
    
    if not os.path.exists(characters_dir):
        print(f"❌ Characters directory not found: {characters_dir}")
        return False
    
    character_files = [f for f in os.listdir(characters_dir) if f.endswith('.json')]
    print(f"Found {len(character_files)} character files")
    
    all_valid = True
    for filename in character_files:
        filepath = os.path.join(characters_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check required fields
            if 'name' not in data:
                print(f"❌ {filename} missing 'name' field")
                all_valid = False
                continue
                
            if 'type' not in data:
                print(f"❌ {filename} missing 'type' field")
                all_valid = False
                continue
                
            if 'abilities' not in data:
                print(f"❌ {filename} missing 'abilities' field")
                all_valid = False
                continue
            
            # Check that abilities is a list
            if not isinstance(data['abilities'], list):
                print(f"❌ {filename} 'abilities' is not a list")
                all_valid = False
                continue
            
            # Check each ability has the right structure
            for i, ability in enumerate(data['abilities']):
                if not isinstance(ability, dict):
                    print(f"❌ {filename} ability {i} is not a dictionary")
                    all_valid = False
                    continue
                
                # Check for required ability fields
                if 'type' not in ability and 'description' not in ability:
                    print(f"❌ {filename} ability {i} has neither 'type' nor 'description'")
                    all_valid = False
                    continue
            
            # Check for other expected fields
            if 'traits' in data:
                print(f"✅ {filename} has traits: {data['traits']}")
            if 'attack' in data:
                print(f"✅ {filename} has attack: {data['attack']}")
            if 'health' in data:
                print(f"✅ {filename} has health: {data['health']}")
            if 'deck_type' in data:
                print(f"✅ {filename} has deck_type: {data['deck_type']}")
            
            print(f"✅ {filename} structure is valid")
            
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            all_valid = False
    
    return all_valid

def test_abilities_examples():
    """Test specific examples to ensure ability structure is correct"""
    characters_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cards', 'characters')
    
    examples = {
        "zeus.json": {
            "expected_abilities": 2,
            "primary_type": "Ranged",
            "primary_has_gold": False,
            "secondary_has_gold": True
        },
        "anne-bunny.json": {
            "expected_abilities": 1,
            "primary_type": "Hunt",
            "primary_has_gold": True,
            "secondary_has_gold": False
        }
    }
    
    all_valid = True
    for filename, expectations in examples.items():
        filepath = os.path.join(characters_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            abilities = data.get('abilities', [])
            
            # Check number of abilities
            if len(abilities) != expectations["expected_abilities"]:
                print(f"❌ {filename} has {len(abilities)} abilities, expected {expectations['expected_abilities']}")
                all_valid = False
                continue
            
            # Check primary ability
            if len(abilities) > 0:
                primary = abilities[0]
                if expectations["primary_type"] and primary.get("type") != expectations["primary_type"]:
                    print(f"❌ {filename} primary ability type is '{primary.get('type')}', expected '{expectations['primary_type']}'")
                    all_valid = False
                
                if expectations["primary_has_gold"]:
                    if "gold_description" not in primary or not primary["gold_description"]:
                        print(f"❌ {filename} primary ability missing gold_description")
                        all_valid = False
                else:
                    if "gold_description" in primary and primary["gold_description"]:
                        print(f"❌ {filename} primary ability has unexpected gold_description: {primary['gold_description']}")
                        all_valid = False
            
            # Check secondary ability if it exists
            if len(abilities) > 1 and expectations["secondary_has_gold"] is not None:
                secondary = abilities[1]
                if expectations["secondary_has_gold"]:
                    if "gold_description" not in secondary or not secondary["gold_description"]:
                        print(f"❌ {filename} secondary ability missing gold_description")
                        all_valid = False
                else:
                    if "gold_description" in secondary and secondary["gold_description"]:
                        print(f"❌ {filename} secondary ability has unexpected gold_description: {secondary['gold_description']}")
                        all_valid = False
            
            print(f"✅ {filename} abilities match expectations")
            
        except Exception as e:
            print(f"❌ Error testing {filename}: {e}")
            all_valid = False
    
    return all_valid

if __name__ == "__main__":
    print("🧪 Testing Character Data Structure...")
    print("=" * 50)
    structure_ok = test_character_data_structure()
    print()
    print("🧪 Testing Ability Examples...")
    print("=" * 50)
    examples_ok = test_abilities_examples()
    print()
    if structure_ok and examples_ok:
        print("🎉 All tests passed! Character data structure is valid.")
    else:
        print("❌ Some tests failed. Check the output above.")
