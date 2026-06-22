import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Read incoming data from the frontend
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            user_input = json.loads(post_data.decode('utf-8'))
            concept = user_input.get('concept', 'General Design')

            # 2. Get and clean the API key from Vercel Environment Variables
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("Server configuration error: GEMINI_API_KEY is missing.")

            # 3. Formulate the system instruction for Gemini
            system_instruction = (
                "You are an expert logo designer and prompt engineer for text-to-image AI tools like Midjourney and DALL-E 3. "
                f"The user needs branding assets for: '{concept}'. "
                "Generate exactly 5 highly detailed, distinct prompt options. "
                "Focus on minimalist, elegant, clean vector aesthetics, solid backgrounds, and clear geometric shapes. "
                "Respond ONLY with a raw JSON array of 5 strings. No markdown, no explanations."
            )

            # 4. Prepare the API request to Google Gemini
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": system_instruction}]}]
            }
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

            # 5. Send request and process the response
            try:
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    ai_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Success Response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"response": ai_text}).encode('utf-8'))

            except urllib.error.HTTPError as e:
                # Catch specific Google API errors (like 400 Bad Request due to a bad key)
                error_info = e.read().decode('utf-8')
                raise Exception(f"Google API rejected the request. Details: {error_info}")

        except Exception as e:
            # General Error Handler
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))