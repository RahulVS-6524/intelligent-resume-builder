import requests
import json
import socket

def test_github_connection():
    print("=" * 60)
    print("TEST 1: Testing GitHub API Connection")
    print("=" * 60)
    
    # Test DNS resolution
    try:
        ip = socket.gethostbyname('api.github.com')
        print(f"✅ DNS Resolution: api.github.com -> {ip}")
    except Exception as e:
        print(f"❌ DNS Error: {e}")
    
    # Test basic connectivity
    try:
        response = requests.get(
            "https://api.github.com", 
            timeout=5,
            headers={"User-Agent": "Python-Requests"}
        )
        print(f"✅ GitHub API Status: {response.status_code}")
        print(f"   Rate Limit: {response.headers.get('X-RateLimit-Remaining', 'Unknown')} remaining")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
    
    # Test octocat's repositories
    print("\n" + "-" * 40)
    print("Testing octocat's repositories...")
    try:
        response = requests.get(
            "https://api.github.com/users/octocat/repos",
            timeout=5,
            headers={"User-Agent": "Python-Requests"}
        )
        if response.status_code == 200:
            repos = response.json()
            print(f"✅ Success! Found {len(repos)} repositories")
            if repos:
                print(f"   First repo: {repos[0]['name']}")
                print(f"   Languages URL: {repos[0]['languages_url']}")
        elif response.status_code == 403:
            print(f"❌ Rate Limited: {response.text[:200]}")
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_fastapi_endpoint():
    print("\n" + "=" * 60)
    print("TEST 2: Testing Your FastAPI Endpoint")
    print("=" * 60)
    
    # Test payload
    test_payload = {
        "github_username": "octocat",
        "job_description_text": "Looking for a Python developer with experience in FastAPI"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/generate_resume",
            json=test_payload,
            timeout=10
        )
        print(f"✅ Server Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server!")
        print("   Make sure your server is running with:")
        print("   python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_your_github():
    print("\n" + "=" * 60)
    print("TEST 3: Test with a Different GitHub Username")
    print("=" * 60)
    
    # Try with a different username
    test_payload = {
        "github_username": "torvalds",  # Linus Torvalds
        "job_description_text": "C programmer needed for Linux kernel development"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/generate_resume",
            json=test_payload,
            timeout=10
        )
        print(f"✅ Server Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 GitHub API Connection Tester")
    print("=" * 60)
    
    test_github_connection()
    
    # Ask if they want to test the FastAPI endpoint
    print("\n" + "=" * 60)
    response = input("Do you want to test your FastAPI endpoint? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        test_fastapi_endpoint()
        test_with_your_github()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")