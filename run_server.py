#!/usr/bin/env python3
"""
ESP32-CAM Image Upload Server
Run this script to start the FastAPI server
"""

import uvicorn
from main import app
from config import HOST, PORT

if __name__ == "__main__":
    print("🚀 Starting ESP32-CAM Image Upload Server...")
    print(f"📡 Server will run on: http://{HOST}:{PORT}")
    print("📸 Upload endpoint: http://localhost:8000/upload")
    print("🖼️  View images: Open frontend.html in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
