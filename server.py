#!/usr/bin/env python3
"""
Simple HTTP server for the Critical Mineral Explorer website.
This serves the website locally and handles CORS issues.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # Change to the directory containing the website files
    website_dir = Path(__file__).parent
    os.chdir(website_dir)
    
    PORT = 8080
    
    # Find an available port
    while True:
        try:
            with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
                print(f"🌐 Critical Mineral Explorer server starting...")
                print(f"📍 Serving at: http://localhost:{PORT}")
                print(f"📁 Directory: {website_dir}")
                print(f"🚀 Opening browser...")
                
                # Open browser automatically
                webbrowser.open(f'http://localhost:{PORT}')
                
                print(f"✅ Server is running. Press Ctrl+C to stop.")
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                PORT += 1
                if PORT > 8090:
                    print("❌ Could not find an available port")
                    return
            else:
                raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

