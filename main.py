import os
import sys
import requests
import base64
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import argparse
from flask import Flask, request, jsonify

# You'll need to install these packages:
# pip install openai requests pillow flask

from openai import OpenAI

class GrokImageGenerator:
    """Complete Grok 2 Image Generation client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Grok Image Generator
        
        Args:
            api_key: Your xAI API key. If None, will try to get from XAI_API_KEY environment variable
        """
        # Replace with your actual API key
        self.api_key = api_key or "xai-wxr9EEv2LIgSUkUSpUq9j8fWUPoEmxRf5cBXOTj5pzrzlqWwsraw2amkVTVLmXDfViOhdgKLddq08pms"
        
        if self.api_key == "xai-YOUR_API_KEY_HERE":
            # Try to get from environment variable as fallback
            env_key = os.getenv("XAI_API_KEY")
            if env_key:
                self.api_key = env_key
            else:
                print("⚠️  Please set your API key in the code or XAI_API_KEY environment variable")
                print("   Get your API key from: https://console.x.ai/team/api-keys")
                sys.exit(1)
        
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=self.api_key
        )
        
        # Create output directory
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✅ Grok Image Generator initialized")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
    
    def generate_images(
        self, 
        prompt: str, 
        count: int = 1, 
        format_type: str = "url",
        save_images: bool = True
    ) -> Dict[str, Any]:
        """
        Generate images using Grok 2 Image model
        
        Args:
            prompt: Description of the image you want to generate
            count: Number of images to generate (1-10)
            format_type: "url" for image URLs or "b64_json" for base64 encoded images
            save_images: Whether to automatically save generated images
            
        Returns:
            Dictionary containing response data and metadata
        """
        print(f"\n🎨 Generating {count} image(s) with prompt: '{prompt}'")
        
        try:
            response = self.client.images.generate(
                model="grok-2-image",
                prompt=prompt,
                n=count,
                response_format=format_type
            )
            
            result = {
                'success': True,
                'original_prompt': prompt,
                'count': len(response.data),
                'images': [],
                'timestamp': datetime.now().isoformat()
            }
            
            for i, image_data in enumerate(response.data):
                image_info = {
                    'index': i + 1,
                    'revised_prompt': image_data.revised_prompt,
                    'url': getattr(image_data, 'url', None),
                    'b64_json': getattr(image_data, 'b64_json', None),
                    'saved_path': None
                }
                
                # Auto-save if requested
                if save_images:
                    if format_type == "url" and image_info['url']:
                        filename = self._generate_filename(prompt, i + 1, "jpg")
                        if self.save_image_from_url(image_info['url'], filename):
                            image_info['saved_path'] = str(filename)
                    elif format_type == "b64_json" and image_info['b64_json']:
                        filename = self._generate_filename(prompt, i + 1, "jpg")
                        if self.save_image_from_b64(image_info['b64_json'], filename):
                            image_info['saved_path'] = str(filename)
                
                result['images'].append(image_info)
            
            self._print_results(result)
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'original_prompt': prompt
            }
            print(f"❌ Error generating images: {e}")
            return error_result
    
    def save_image_from_url(self, image_url: str, filename: Path) -> bool:
        """Download and save an image from URL"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"💾 Saved: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving image from URL: {e}")
            return False
    
    def save_image_from_b64(self, b64_string: str, filename: Path) -> bool:
        """Save base64 encoded image to file"""
        try:
            # Remove data:image/jpeg;base64, prefix if present
            if b64_string.startswith('data:image'):
                b64_string = b64_string.split(',', 1)[1]
            
            image_data = base64.b64decode(b64_string)
            
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            print(f"💾 Saved: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving base64 image: {e}")
            return False
    
    def _generate_filename(self, prompt: str, index: int, extension: str) -> Path:
        """Generate a safe filename from prompt"""
        # Clean prompt for filename
        safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_prompt = safe_prompt.replace(' ', '_')[:50]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_prompt}_{timestamp}_{index:02d}.{extension}"
        
        return self.output_dir / filename
    
    def _print_results(self, result: Dict[str, Any]):
        """Print formatted results"""
        if not result['success']:
            return
            
        print(f"\n✅ Successfully generated {result['count']} image(s)")
        print(f"📝 Original prompt: {result['original_prompt']}")
        
        for img in result['images']:
            print(f"\n🖼️  Image {img['index']}:")
            print(f"   Revised prompt: {img['revised_prompt']}")
            if img['url']:
                print(f"   URL: {img['url']}")
            if img['saved_path']:
                print(f"   Saved to: {img['saved_path']}")
    
    def save_session_log(self, results: List[Dict[str, Any]], filename: str = None):
        """Save session results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_log_{timestamp}.json"
        
        log_path = self.output_dir / filename
        
        with open(log_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📋 Session log saved to: {log_path}")

def interactive_mode():
    """Run the application in interactive mode"""
    print("🎨 Welcome to Grok 2 Image Generator!")
    print("=" * 50)
    
    generator = GrokImageGenerator()
    session_results = []
    
    while True:
        print("\n" + "="*50)
        print("What would you like to do?")
        print("1. Generate images from text prompt")
        print("2. View session history")
        print("3. Save session log")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            prompt = input("\n📝 Enter your image prompt: ").strip()
            if not prompt:
                print("❌ Please enter a valid prompt")
                continue
            
            try:
                count = int(input("🔢 How many images? (1-10, default 1): ") or "1")
                count = max(1, min(10, count))
            except ValueError:
                count = 1
            
            format_choice = input("📁 Format (url/b64): ").strip().lower()
            format_type = "b64_json" if format_choice == "b64" else "url"
            
            result = generator.generate_images(prompt, count, format_type)
            session_results.append(result)
        
        elif choice == "2":
            if not session_results:
                print("📭 No images generated in this session yet")
                continue
            
            print(f"\n📊 Session History ({len(session_results)} generations):")
            for i, result in enumerate(session_results, 1):
                status = "✅" if result['success'] else "❌"
                prompt = result['original_prompt'][:50] + "..." if len(result['original_prompt']) > 50 else result['original_prompt']
                count = result.get('count', 0) if result['success'] else 0
                print(f"  {i}. {status} '{prompt}' ({count} images)")
        
        elif choice == "3":
            if session_results:
                generator.save_session_log(session_results)
            else:
                print("📭 No session data to save")
        
        elif choice == "4":
            if session_results:
                save_log = input("💾 Save session log before exit? (y/n): ").strip().lower()
                if save_log == 'y':
                    generator.save_session_log(session_results)
            
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-4")

def command_line_mode():
    """Run the application in command line mode"""
    parser = argparse.ArgumentParser(description='Generate images using Grok 2 Image model')
    parser.add_argument('prompt', help='Text prompt for image generation')
    parser.add_argument('--count', '-n', type=int, default=1, help='Number of images to generate (1-10)')
    parser.add_argument('--format', '-f', choices=['url', 'b64'], default='url', help='Output format')
    parser.add_argument('--no-save', action='store_true', help="Don't save images automatically")
    
    args = parser.parse_args()
    
    generator = GrokImageGenerator()
    format_type = "b64_json" if args.format == "b64" else "url"
    
    result = generator.generate_images(
        prompt=args.prompt,
        count=args.count,
        format_type=format_type,
        save_images=not args.no_save
    )
    
    return result

# Predefined example prompts for quick testing
EXAMPLE_PROMPTS = [
    "A majestic dragon flying over a medieval castle at sunset",
    "A futuristic city with flying cars and neon lights",
    "A cute robot cat sitting in a flower garden",
    "A magical forest with glowing mushrooms and fairy lights",
    "A space station orbiting a colorful nebula",
    "A steampunk airship floating above the clouds",
    "A cozy coffee shop on a rainy day with warm lighting",
    "A cyberpunk street market with holographic displays"
]

def quick_demo():
    """Run a quick demo with example prompts"""
    print("🚀 Quick Demo Mode - Generating sample images")
    print("=" * 50)
    
    generator = GrokImageGenerator()
    
    print("\n🎲 Available example prompts:")
    for i, prompt in enumerate(EXAMPLE_PROMPTS, 1):
        print(f"  {i}. {prompt}")
    
    try:
        choice = int(input(f"\nChoose a prompt (1-{len(EXAMPLE_PROMPTS)}): ")) - 1
        if 0 <= choice < len(EXAMPLE_PROMPTS):
            selected_prompt = EXAMPLE_PROMPTS[choice]
            result = generator.generate_images(selected_prompt, count=1)
            return result
        else:
            print("❌ Invalid choice")
    except ValueError:
        print("❌ Please enter a valid number")

# Flask API server code
app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def api_generate_images():
    """API endpoint to generate images from prompt"""
    data = request.json
    
    prompt = data.get('prompt')
    count = data.get('count', 1)
    format_type = data.get('format', 'url')
    save_images = data.get('save_images', True)
    
    if not prompt:
        return jsonify({'success': False, 'error': 'Prompt is required'}), 400
    
    try:
        generator = GrokImageGenerator()
        result = generator.generate_images(prompt, count, format_type, save_images)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def api_server_mode():
    """Run the application as a Flask API server"""
    app = Flask(__name__)
    generator = GrokImageGenerator()
    
    @app.route('/generate-image', methods=['POST'])
    def generate_image():
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        if 'prompt' not in data:
            return jsonify({"error": "Prompt is required"}), 400
        
        prompt = data.get('prompt')
        count = min(max(1, data.get('count', 1)), 10)  # Between 1-10
        format_type = data.get('format', 'url')
        if format_type not in ['url', 'b64_json']:
            format_type = 'url'
        
        save_images = data.get('save_images', True)
        
        result = generator.generate_images(
            prompt=prompt,
            count=count,
            format_type=format_type,
            save_images=save_images
        )
        
        return jsonify(result)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "service": "Grok 2 Image Generator API"})
    
    print("🚀 Starting Grok Image Generator API server on port 8081")
    app.run(host='0.0.0.0', port=8081, debug=False)

if __name__ == "__main__":
    print("🎨 Grok 2 Image Generator")
    print("========================")
    
    # Check if command line arguments are provided
    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            api_server_mode()
        else:
            command_line_mode()
    else:
        print("\nChoose mode:")
        print("1. Interactive mode")
        print("2. Quick demo")
        print("3. API Server mode")
        print("4. Exit")
        
        mode = input("\nEnter choice (1-4): ").strip()
        
        if mode == "1":
            interactive_mode()
        elif mode == "2":
            quick_demo()
        elif mode == "3":
            api_server_mode()
        elif mode == "4":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice, starting interactive mode...")
            interactive_mode()