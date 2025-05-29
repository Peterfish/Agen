from goat_storytelling_agent.storytelling_agent import StoryAgent

# Initialize StoryAgent with KoboldCpp
writer = StoryAgent(
    backend_uri="http://localhost:5001/v1",
    form='novel',
    extra_options={
        'temperature': 0.8,
        'top_p': 0.9,
        'repetition_penalty': 1.1,
        'top_k': 40,
    },
    scene_extra_options={
        'temperature': 0.9,  # Higher creativity for scenes
    }
)

# Example 1: Generate complete story
print("Generating complete story...")
novel_scenes = writer.generate_story('treasure hunt in a jungle')

# Save results
with open('generated_novel.txt', 'w', encoding='utf-8') as f:
    for i, scene in enumerate(novel_scenes):
        f.write(f"\n\n{'='*50}\n")
        f.write(f"SCENE {i+1}\n")
        f.write(f"{'='*50}\n\n")
        f.write(scene)

print(f"Generated {len(novel_scenes)} scenes. Saved to generated_novel.txt")

# Example 2: Step-by-step generation
print("\n\nStep-by-step generation example:")
topic = 'a detective story in cyberpunk Tokyo'

# Create book specification
msgs, book_spec = writer.init_book_spec(topic)
print("Book Specification:")
print(book_spec)
