#!/usr/bin/env python3
"""
Version synchronization utility for the observables package.
This script updates version numbers across all project files.
"""

import re
import sys
from pathlib import Path

def update_version_files(new_version: str) -> None:
    """Update version numbers in all project files."""
    
    # Files to update with their patterns
    files_to_update = [
        {
            "path": "observables/_version.py",
            "pattern": r'__version__ = "[^"]*"',
            "replacement": f'__version__ = "{new_version}"'
        },
        {
            "path": "observables/_version.py",
            "pattern": r'__version_tuple__ = \([^)]*\)',
            "replacement": f'__version_tuple__ = {tuple(map(int, new_version.split(".")))}'
        },
        {
            "path": "observables/__init__.py",
            "pattern": r'__version__ = "[^"]*"',
            "replacement": f'__version__ = "{new_version}"'
        },
        {
            "path": "observables/__init__.py",
            "pattern": r'__version_tuple__ = \([^)]*\)',
            "replacement": f'__version_tuple__ = {tuple(map(int, new_version.split(".")))}'
        },
        {
            "path": "setup.py",
            "pattern": r'return "[^"]*"  # fallback version',
            "replacement": f'return "{new_version}"  # fallback version'
        }
    ]
    
    print(f"Updating version to {new_version}...")
    
    for file_info in files_to_update:
        file_path = Path(file_info["path"])
        if not file_path.exists():
            print(f"⚠️  Warning: {file_path} not found, skipping...")
            continue
            
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply replacement
            old_content = content
            content = re.sub(
                file_info["pattern"], 
                file_info["replacement"], 
                content
            )
            
            # Write back if changed
            if content != old_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated {file_path}")
            else:
                print(f"ℹ️  No changes needed in {file_path}")
                
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    print("\nVersion update complete!")
    print(f"\nTo use git-based versioning with setuptools-scm:")
    print("1. Install: pip install setuptools-scm[toml]")
    print("2. Create git tag: git tag v{new_version}")
    print("3. Push tag: git push origin v{new_version}")
    print("\nOr manually update observables/_version.py when needed.")

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 0.2.2")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format (simple check)
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Error: Version must be in format X.Y.Z (e.g., 0.2.2)")
        sys.exit(1)
    
    update_version_files(new_version)

if __name__ == "__main__":
    main()
