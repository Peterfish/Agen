# GOAT-Storytelling-Agent: KoboldCpp Edition

A modified version of [GOAT-AI's Storytelling Agent](https://github.com/GOAT-AI/storytelling-agent) specifically designed to work with **Mistral Large** models through **KoboldCpp**.

## Features

- 🚀 Optimized for **Mistral Large Q4_K_M** via KoboldCpp
- 📚 Complete novel/story generation from a single topic
- 🎭 Step-by-step control over story creation process
- 🌏 Full Unicode support (including Thai language)
- 💾 Minimal dependencies (only `requests` library needed)

## Requirements

- Python 3.7+
- [KoboldCpp](https://github.com/LostRuins/koboldcpp) running with Mistral Large model
- ~75-80GB VRAM/RAM for Mistral Large Q4_K_M

## Quick Start

### 1. Install KoboldCpp and Load Model

Download and run KoboldCpp with Mistral Large:
```bash
./koboldcpp --model Mistral-Large-Instruct-2411-Q4_K_M.gguf --port 5001
```

### 2. Install Story Agent

```bash
pip install -r requirements.txt
```

### 3. Test Connection

```bash
python test_connection.py
```

### 4. Generate Your First Story

```python
from goat_storytelling_agent.storytelling_agent import StoryAgent

writer = StoryAgent()
story = writer.generate_story('a detective story in cyberpunk Bangkok')
```

## License

MIT License - see LICENSE file
