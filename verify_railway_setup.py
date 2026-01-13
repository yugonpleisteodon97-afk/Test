#!/usr/bin/env python3
"""
Verify Railway deployment setup.

This script checks if all necessary files and configurations are in place
for Railway deployment.
"""

import os
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output (if supported)."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors for Windows console."""
        cls.GREEN = ''
        cls.RED = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.END = ''


# Disable colors on Windows by default
if sys.platform == 'win32':
    Colors.disable()


def check_file(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"  {Colors.GREEN}OK{Colors.END} {description}: {filepath}")
        return True
    else:
        print(f"  {Colors.RED}MISSING{Colors.END} {description}: {filepath}")
        return False


def check_file_content(filepath, content, description):
    """Check if a file contains specific content."""
    try:
        with open(filepath, 'r') as f:
            file_content = f.read()
            if content in file_content:
                print(f"  {Colors.GREEN}OK{Colors.END} {description}")
                return True
            else:
                print(f"  {Colors.YELLOW}WARNING{Colors.END} {description}")
                return False
    except FileNotFoundError:
        print(f"  {Colors.RED}MISSING{Colors.END} {description} - File not found")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Railway Deployment Setup Verification")
    print("=" * 60)
    print()
    
    all_checks = []
    
    # Check required Railway files
    print(f"{Colors.BLUE}1. Checking Railway Configuration Files{Colors.END}")
    all_checks.append(check_file("Procfile", "Procfile"))
    all_checks.append(check_file("railway.toml", "Railway config"))
    all_checks.append(check_file("nixpacks.toml", "Build config"))
    all_checks.append(check_file(".railwayignore", "Railway ignore"))
    print()
    
    # Check application files
    print(f"{Colors.BLUE}2. Checking Application Files{Colors.END}")
    all_checks.append(check_file("requirements.txt", "Python dependencies"))
    all_checks.append(check_file("app/__init__.py", "Flask app factory"))
    all_checks.append(check_file("app/config.py", "App configuration"))
    print()
    
    # Check config.py for Railway compatibility
    print(f"{Colors.BLUE}3. Checking Configuration Compatibility{Colors.END}")
    all_checks.append(check_file_content(
        "app/config.py", 
        "PORT = int(os.environ.get('PORT'", 
        "PORT environment variable support"
    ))
    all_checks.append(check_file_content(
        "app/config.py",
        "postgresql://",
        "PostgreSQL URL handling"
    ))
    print()
    
    # Check documentation
    print(f"{Colors.BLUE}4. Checking Documentation{Colors.END}")
    all_checks.append(check_file("RAILWAY_DEPLOYMENT.md", "Deployment guide"))
    all_checks.append(check_file("README_RAILWAY.md", "Quick start guide"))
    all_checks.append(check_file("env.railway.example", "Environment template"))
    print()
    
    # Check helper scripts
    print(f"{Colors.BLUE}5. Checking Helper Scripts{Colors.END}")
    all_checks.append(check_file("generate_railway_keys.py", "Key generator"))
    print()
    
    # Check .gitignore
    print(f"{Colors.BLUE}6. Checking .gitignore{Colors.END}")
    all_checks.append(check_file_content(
        ".gitignore",
        "railway_keys.txt",
        "Railway keys excluded from git"
    ))
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(all_checks)
    total = len(all_checks)
    
    if passed == total:
        print(f"{Colors.GREEN}All checks passed! ({passed}/{total}){Colors.END}")
        print()
        print("Your application is ready for Railway deployment!")
        print()
        print("Next steps:")
        print("1. Run: python generate_railway_keys.py")
        print("2. Push to GitHub: git push origin main")
        print("3. Follow instructions in README_RAILWAY.md")
        print()
        return 0
    else:
        print(f"{Colors.RED}Some checks failed ({passed}/{total} passed){Colors.END}")
        print()
        print("Please fix the issues above before deploying.")
        print("See RAILWAY_DEPLOYMENT.md for detailed setup instructions.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
