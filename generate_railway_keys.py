#!/usr/bin/env python3
"""
Generate secure keys for Railway deployment.

This script generates secure random keys needed for the Railway environment variables.
Run this script and copy the output to your Railway service variables.
"""

import secrets
import sys


def generate_key(length=32):
    """Generate a secure random key."""
    return secrets.token_urlsafe(length)


def main():
    print("=" * 60)
    print("Secure Keys Generator for Railway Deployment")
    print("=" * 60)
    print()
    print("Copy these values to your Railway environment variables:")
    print()
    print("-" * 60)
    
    # Generate keys
    secret_key = generate_key(32)
    jwt_secret = generate_key(32)
    encryption_key = generate_key(32)
    
    print(f"SECRET_KEY={secret_key}")
    print()
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    print("-" * 60)
    print()
    print("How to use these keys:")
    print()
    print("1. Go to Railway Dashboard")
    print("2. Select your service (radar-web, radar-worker, or radar-beat)")
    print("3. Click 'Variables' tab")
    print("4. Click 'Raw Editor'")
    print("5. Add the keys above to your environment variables")
    print()
    print("IMPORTANT: Add these SAME keys to ALL THREE services!")
    print("   - radar-web")
    print("   - radar-worker")
    print("   - radar-beat")
    print()
    print("=" * 60)
    print()
    
    # Ask if user wants to save to a file
    try:
        response = input("Save these keys to a file? (y/n): ").strip().lower()
        if response == 'y':
            with open('railway_keys.txt', 'w') as f:
                f.write(f"SECRET_KEY={secret_key}\n")
                f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
                f.write(f"ENCRYPTION_KEY={encryption_key}\n")
            print("Keys saved to 'railway_keys.txt'")
            print("IMPORTANT: Keep this file secure and DO NOT commit it to git!")
            print()
    except (KeyboardInterrupt, EOFError):
        print("\n\nKeys not saved to file.")
        sys.exit(0)


if __name__ == "__main__":
    main()
