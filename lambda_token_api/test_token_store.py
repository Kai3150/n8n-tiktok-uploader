#!/usr/bin/env python3
"""
Local test script for token_store.py functionality
Run this locally to test S3 token operations before deploying to Lambda
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the path so we can import token_store
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from token_store import TokenStore

def test_token_operations():
    """Test basic token store operations"""
    print("=== Testing TokenStore Operations ===\n")
    
    # Test 1: List accounts (should be empty initially or show existing)
    print("1. Listing existing accounts:")
    accounts = TokenStore.list_accounts()
    print(f"   Found accounts: {accounts}")
    print()
    
    # Test 2: Check if specific account exists
    test_open_id = "test_user_123"
    print(f"2. Checking if account '{test_open_id}' exists:")
    exists = TokenStore.has_account(test_open_id)
    print(f"   Account exists: {exists}")
    print()
    
    # Test 3: Try to get access token for non-existent account
    print(f"3. Getting access token for '{test_open_id}':")
    token = TokenStore.get_access_token(test_open_id)
    print(f"   Access token: {token}")
    print()
    
    # Test 4: Save a mock token
    print("4. Saving a mock token:")
    mock_token = {
        "access_token": "mock_access_token_123",
        "refresh_token": "mock_refresh_token_123", 
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "user.info.basic,video.publish",
        "open_id": test_open_id
    }
    
    try:
        saved_token = TokenStore.save_token(mock_token, test_open_id)
        print(f"   Token saved successfully")
        print(f"   Expires at: {datetime.fromtimestamp(saved_token.get('expires_at', 0))}")
    except Exception as e:
        print(f"   Error saving token: {e}")
    print()
    
    # Test 5: Retrieve the saved token
    print("5. Retrieving saved token:")
    retrieved_token = TokenStore.load_token(test_open_id)
    if retrieved_token:
        print(f"   Token retrieved successfully")
        print(f"   Access token: {retrieved_token.get('access_token', 'N/A')}")
        print(f"   Expires at: {datetime.fromtimestamp(retrieved_token.get('expires_at', 0))}")
    else:
        print("   No token found")
    print()
    
    # Test 6: Get access token (should return the saved one if not expired)
    print("6. Getting access token after saving:")
    access_token = TokenStore.get_access_token(test_open_id)
    print(f"   Access token: {access_token}")
    print()
    
    # Test 7: List accounts again (should now include our test account)
    print("7. Listing accounts after saving:")
    accounts = TokenStore.list_accounts()
    print(f"   Found accounts: {accounts}")
    print()
    
    # Test 8: Delete the test account
    print(f"8. Deleting test account '{test_open_id}':")
    deleted = TokenStore.delete_account(test_open_id)
    print(f"   Account deleted: {deleted}")
    print()
    
    # Test 9: Verify deletion
    print("9. Verifying deletion:")
    accounts = TokenStore.list_accounts()
    print(f"   Remaining accounts: {accounts}")
    exists = TokenStore.has_account(test_open_id)
    print(f"   Test account still exists: {exists}")
    print()

def test_s3_connection():
    """Test S3 connection"""
    print("=== Testing S3 Connection ===\n")
    
    try:
        # Try to load tokens (this will test S3 connectivity)
        tokens = TokenStore._load_raw_tokens()
        print(f"✓ S3 connection successful")
        print(f"  Current tokens in S3: {list(tokens.keys()) if tokens else 'None'}")
    except Exception as e:
        print(f"✗ S3 connection failed: {e}")
        print("  Please check:")
        print("  - AWS credentials are configured")
        print("  - S3 bucket 'tiktok-token-store' exists")
        print("  - Proper IAM permissions for S3 access")

if __name__ == "__main__":
    print("TikTok Token Store Test Script")
    print("=" * 40)
    print()
    
    # Test S3 connection first
    test_s3_connection()
    print()
    
    # Test token operations
    test_token_operations()
    
    print("=== Test Complete ===")