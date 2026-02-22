# Create a file test_github.py in your project root
import requests
import socket

def test_github_connection():
    print("1. Testing DNS resolution...")
    try:
        ip = socket.gethostbyname('api.github.com')
        print(f"   ✅ GitHub API resolves to: {ip}")
    except Exception as e:
        print(f"   ❌ DNS error: {e}")
    
    print("\n2. Testing basic connectivity...")
    try:
        response = requests.get("https://api.github.com", timeout=5)
        print(f"   ✅ GitHub API responded with status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

if __name__ == "__main__":
    test_github_connection()