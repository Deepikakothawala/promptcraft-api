import os
import json
import http.server
import urllib.request
import urllib.error

class handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Read incoming user data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            user_input = json.loads(post_data.decode('utf-8'))
            concept = user_input.get('concept', 'General Business')

            # 2. Define the hidden system prompt
            system_instructions = (
                "You are an expert logo designer and prompt engineer for text-to-image AIs like Midjourney and DALL-E 3. "
                f"The user wants a logo/brand asset for: '{concept}'. "
                "Generate exactly 5 highly detailed, distinct prompt options. "
                "Format your response STRICTLY as a raw JSON array of strings containing exactly 5 items, with NO markdown block formatting."
            )

            # 3. Get the API key and remove any accidental blank spaces
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            
            if not api_key:
                raise ValueError("The API Key is missing from Vercel Environment Variables.")

            # 4. Prepare payload for Gemini API using the correct, updated model name
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": system_instructions}]
                }]
            }

            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Vercel-Serverless-App'
                }
            )
            
            # 5. Send request to Google
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                ai_response_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Send success response to frontend
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*') 
                self.end_headers()
                self.wfile.write(json.dumps({"response": ai_response_text}).encode('utf-8'))
                
        # 6. EXTREME ERROR CATCHING: Show exact Google error
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Google API rejected the request. Details: {error_body}"}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
