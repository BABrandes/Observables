#!/usr/bin/env python3
"""
Advanced version management for the observables package.
Supports automatic version increments and Git integration.
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

class VersionManager:
    """Manages version numbers with Git integration."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_file = project_root / "observables" / "_version.py"
        
    def get_current_version(self) -> str:
        """Get current version from _version.py."""
        if not self.version_file.exists():
            raise FileNotFoundError(f"Version file not found: {self.version_file}")
            
        with open(self.version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    match = re.search(r'__version__ = "([^"]*)"', line)
                    if match:
                        return match.group(1)
        
        raise ValueError("Could not parse version from _version.py")
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into components."""
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
            raise ValueError(f"Invalid version components: {version}")
    
    def increment_version(self, version: str, increment_type: str = 'patch') -> str:
        """Increment version based on type."""
        major, minor, patch = self.parse_version(version)
        
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        elif increment_type == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid increment type: {increment_type}")
        
        return f"{major}.{minor}.{patch}"
    
    def update_version(self, new_version: str) -> None:
        """Update version across all project files."""
        # Run the existing update script
        result = subprocess.run([
            sys.executable, 
            str(self.project_root / "update_version.py"), 
            new_version
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Version update failed: {result.stderr}")
        
        print(f"✅ Version updated to {new_version}")
    
    def get_git_status(self) -> dict:
        """Get current Git status information."""
        try:
            # Get current branch
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip()
            
            # Get commit count since last tag
            commit_count = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip()
            
            # Get last tag
            last_tag = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip()
            
            return {
                'branch': branch,
                'commit_count': commit_count,
                'last_tag': last_tag
            }
        except subprocess.CalledProcessError:
            return {}
    
    def auto_increment(self, increment_type: str = 'patch', 
                      commit_message: Optional[str] = None) -> str:
        """Automatically increment version and optionally commit."""
        current_version = self.get_current_version()
        new_version = self.increment_version(current_version, increment_type)
        
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
        
        # Update version files
        self.update_version(new_version)
        
        # Git operations
        git_status = self.get_git_status()
        if git_status:
            print(f"Git branch: {git_status['branch']}")
            print(f"Commits since last tag: {git_status['commit_count']}")
        
        # Add version files to Git
        subprocess.run(['git', 'add', 'observables/_version.py', 'observables/__init__.py', 'setup.py'], 
                      cwd=self.project_root)
        
        if commit_message:
            # Commit with custom message
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.project_root)
            print(f"✅ Committed version {new_version}")
        else:
            print(f"✅ Version files staged for commit")
        
        return new_version
    
    def create_tag(self, version: str, message: Optional[str] = None) -> None:
        """Create a Git tag for the current version."""
        tag_name = f"v{version}"
        tag_message = message or f"Release version {version}"
        
        subprocess.run(['git', 'tag', '-a', tag_name, '-m', tag_message], cwd=self.project_root)
        print(f"✅ Created tag: {tag_name}")
    
    def push_changes(self, push_tags: bool = True) -> None:
        """Push commits and tags to remote."""
        # Push commits
        subprocess.run(['git', 'push'], cwd=self.project_root)
        print("✅ Pushed commits")
        
        # Push tags
        if push_tags:
            subprocess.run(['git', 'push', '--tags'], cwd=self.project_root)
            print("✅ Pushed tags")

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/version_manager.py auto [patch|minor|major] [commit_message]")
        print("  python scripts/version_manager.py increment <version>")
        print("  python scripts/version_manager.py tag <version> [message]")
        print("  python scripts/version_manager.py push")
        sys.exit(1)
    
    project_root = Path(__file__).parent.parent
    manager = VersionManager(project_root)
    
    command = sys.argv[1]
    
    try:
        if command == "auto":
            increment_type = sys.argv[2] if len(sys.argv) > 2 else 'patch'
            commit_message = sys.argv[3] if len(sys.argv) > 3 else None
            
            if increment_type not in ['patch', 'minor', 'major']:
                print("❌ Invalid increment type. Use: patch, minor, or major")
                sys.exit(1)
            
            new_version = manager.auto_increment(increment_type, commit_message)
            print(f"\n🎉 Version {new_version} ready!")
            
        elif command == "increment":
            if len(sys.argv) < 3:
                print("❌ Please provide a version number")
                sys.exit(1)
            manager.update_version(sys.argv[2])
            
        elif command == "tag":
            if len(sys.argv) < 3:
                print("❌ Please provide a version number")
                sys.exit(1)
            message = sys.argv[3] if len(sys.argv) > 3 else None
            manager.create_tag(sys.argv[2], message)
            
        elif command == "push":
            manager.push_changes()
            
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
