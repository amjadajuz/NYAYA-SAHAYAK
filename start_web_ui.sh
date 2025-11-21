#!/bin/bash
# Start the ADK Web UI for AI Advocate

echo "Starting AI Advocate Web UI..."
echo "Open your browser to: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

adk web index:root_agent --port 8000

