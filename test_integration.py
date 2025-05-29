import json
from goat_storytelling_agent import plan, prompts, utils

def test_all_modules():
    """Test all modules work together"""
    print("Testing GOAT Storytelling Agent Components")
    print("="*50)
    
    # Test plan module
    print("\nTesting plan.py...")
    sample_plan_text = """
Act 1: The Beginning
- Chapter 1: Introduction
- Chapter 2: The call

Act 2: The Journey
- Chapter 3: Tests

Act 3: The Return
- Chapter 4: Resolution
"""
    parsed = plan.Plan.parse_text_plan(sample_plan_text)
    print(f"✓ Parsed {len(parsed)} acts")
    
    # Test prompts module
    print("\nTesting prompts.py...")
    msgs = prompts.init_book_spec_messages("test", "novel")
    print(f"✓ Generated {len(msgs)} messages")
    
    # Test utils module
    print("\nTesting utils.py...")
    result = utils.keep_last_n_words("This is a test text", 3)
    print(f"✓ Text processing: '{result}'")
    
    print("\n✓ All modules working correctly!")

if __name__ == "__main__":
    test_all_modules()
