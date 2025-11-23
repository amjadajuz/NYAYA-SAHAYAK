# AI Advocate - Legal Assistant

An AI-powered legal advocate that helps users understand their rights and provides legal information using Google's Agent Development Kit (ADK).

## Features

- Collects necessary information about legal incidents
- Researches relevant legal information using Google Search
- Provides clear guidance about legal rights and options
- Empathetic and professional responses

## Setup

1. Make sure you have the required dependencies installed:
```bash
pip install -r requirements.txt
```

2. The API key is already configured in `index.py`

## Running the Application

### Option 1: Command Line Interface
Run the agent directly from the command line:
```bash
python3 agent.py
```

### Option 2: Web UI (Recommended)
Start the interactive web UI:
```bash
streamlit run app.py
```

Then open your browser to: `http://localhost:8501`

**Note:** The web UI command will run indefinitely. Press `Ctrl+C` to stop it.

## Files

- `index.py` - Main agent configuration and CLI runner
- `README.md` - This file

## Usage Example

When you interact with the AI Advocate, provide details such as:
- Date and time of incident
- Location
- Injuries (if any)
- Police report information
- Witness information
- Driver/vehicle information

The agent will use this information to research and provide relevant legal guidance.

