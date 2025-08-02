#!/usr/bin/env python3
"""
Simple test script for Spotify API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_spotify_login():
    """Test the Spotify login endpoint"""
    print("Testing Spotify login endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/spotify/login")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
            
            if "authorization_url" in data:
                print("✅ Login endpoint working correctly!")
                print(f"Authorization URL: {data['authorization_url']}")
            else:
                print("❌ No authorization URL in response")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_add_endpoint():
    """Test the existing add endpoint"""
    print("\nTesting add endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/add?a=5&b=3")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
            print("✅ Add endpoint working correctly!")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_user_endpoint():
    """Test the user endpoint (should fail without authentication)"""
    print("\nTesting user endpoint (should fail without auth)...")
    
    try:
        response = requests.get(f"{BASE_URL}/spotify/user")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
        else:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
            print("✅ User endpoint correctly requires authentication!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Spotify API Endpoints")
    print("=" * 40)
    
    test_add_endpoint()
    test_spotify_login()
    test_user_endpoint()
    
    print("\n" + "=" * 40)
    print("🎉 Test completed!")
    print("\nTo use the Spotify login:")
    print("1. Set up your .env file with Spotify credentials")
    print("2. Visit the authorization URL returned by the login endpoint")
    print("3. Complete the Spotify OAuth flow") 