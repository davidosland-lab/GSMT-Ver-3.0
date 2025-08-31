#!/usr/bin/env python3
"""
Script to update backend URL in frontend files
Usage: python update_backend_url.py https://your-actual-railway-url.up.railway.app
"""

import sys
import re

def update_backend_url(new_url):
    """Update the backend URL in frontend files"""
    
    files_to_update = [
        'global-markets-tracker.html',
        'js/providers.js'
    ]
    
    # Pattern to match the production URL line
    pattern = r"(:\s*['\"])https://backend-production-XXXX\.up\.railway\.app(['\"])"
    replacement = rf"\g<1>{new_url}\g<2>"
    
    print(f"🔄 Updating backend URL to: {new_url}")
    print("=" * 50)
    
    for file_path in files_to_update:
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if URL needs updating
            if 'backend-production-XXXX' in content:
                # Replace the URL
                updated_content = re.sub(pattern, replacement, content)
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print(f"✅ Updated {file_path}")
            else:
                print(f"ℹ️  {file_path} already updated or not found")
                
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    print("\n🎉 Frontend files updated!")
    print(f"Your backend URL: {new_url}")
    print("\nNext steps:")
    print("1. Test your backend: curl {}/api/health".format(new_url))
    print("2. Deploy your frontend to Netlify/Vercel")
    print("3. Test live data in your tracker!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_backend_url.py <RAILWAY_URL>")
        print("Example: python update_backend_url.py https://backend-production-a1b2c3.up.railway.app")
        sys.exit(1)
    
    new_url = sys.argv[1].rstrip('/')
    
    # Validate URL format
    if not new_url.startswith('https://'):
        print("❌ URL must start with https://")
        sys.exit(1)
    
    update_backend_url(new_url)

if __name__ == "__main__":
    main()