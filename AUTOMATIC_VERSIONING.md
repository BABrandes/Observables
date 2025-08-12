# Automatic Version Incrementing Guide

This guide explains how to set up automatic version increments on every commit in your Observables project.

## 🚀 **Quick Start**

### **Option 1: Git Pre-commit Hook (Recommended for Local Development)**

The pre-commit hook automatically increments versions based on your commit message:

```bash
# The hook is already installed and active
# Just commit normally and watch the magic happen!

git add .
git commit -m "fix: resolve binding issue"  # → Patch increment (0.2.6 → 0.2.7)
git commit -m "feat: add new validation"    # → Minor increment (0.2.7 → 0.3.0)
git commit -m "BREAKING CHANGE: new API"     # → Major increment (0.3.0 → 1.0.0)
```

### **Option 2: Manual Version Management**

```bash
# Auto-increment with specific type
make version-auto TYPE=patch    # 0.2.6 → 0.2.7
make version-auto TYPE=minor    # 0.2.6 → 0.3.0
make version-auto TYPE=major    # 0.2.6 → 1.0.0

# Or use the script directly
python scripts/version_manager.py auto minor
```

## 🔧 **How It Works**

### **Pre-commit Hook Logic**

The Git hook analyzes your commit message and determines the version increment:

| Commit Message Pattern | Version Increment | Example |
|----------------------|------------------|---------|
| `BREAKING CHANGE:` or `major:` | **Major** (X.0.0) | `0.2.6` → `1.0.0` |
| `feat:` or `feature:` or `minor:` | **Minor** (0.X.0) | `0.2.6` → `0.3.0` |
| Any other message | **Patch** (0.0.X) | `0.2.6` → `0.2.7` |

### **Semantic Versioning**

- **Major**: Breaking changes, incompatible API changes
- **Minor**: New features, backward-compatible additions
- **Patch**: Bug fixes, backward-compatible patches

## 📋 **Available Commands**

### **Makefile Commands**

```bash
# Manual version update
make version VERSION=0.2.7

# Auto-increment versions
make version-auto TYPE=patch
make version-auto TYPE=minor
make version-auto TYPE=major

# Create Git tags
make version-tag VERSION=0.2.7

# Show all available commands
make help
```

### **Direct Script Usage**

```bash
# Auto-increment with commit
python scripts/version_manager.py auto patch "fix: resolve issue"
python scripts/version_manager.py auto minor "feat: add validation"
python scripts/version_manager.py auto major "BREAKING CHANGE: new API"

# Manual version update
python scripts/version_manager.py increment 0.2.7

# Create tags
python scripts/version_manager.py tag 0.2.7 "Release version 0.2.7"

# Push changes
python scripts/version_manager.py push
```

## 🎯 **Workflow Examples**

### **Daily Development Workflow**

```bash
# 1. Make your changes
# 2. Stage files
git add .

# 3. Commit (version auto-increments)
git commit -m "fix: resolve memory leak in binding system"
# → Version automatically bumped from 0.2.6 to 0.2.7

# 4. Push
git push origin main
```

### **Feature Release Workflow**

```bash
# 1. Add new feature
git add .
git commit -m "feat: add custom validation support"
# → Version automatically bumped from 0.2.7 to 0.3.0

# 2. Create release tag
make version-tag VERSION=0.3.0

# 3. Push everything
git push origin main --tags
```

### **Breaking Change Workflow**

```bash
# 1. Make breaking changes
git add .
git commit -m "BREAKING CHANGE: rename Observable to ReactiveObject"
# → Version automatically bumped from 0.3.0 to 1.0.0

# 2. Update documentation
# 3. Create major release tag
make version-tag VERSION=1.0.0

# 4. Push
git push origin main --tags
```

## 🔄 **GitHub Actions Integration**

The project includes a GitHub Actions workflow that can:

- **Auto-detect** version increment types from commit messages
- **Automatically bump** versions on pushes
- **Create pull requests** for version updates
- **Manual triggering** with custom increment types

### **Workflow Triggers**

- **Push to main/develop**: Auto-version bump
- **Pull requests**: Version validation
- **Manual dispatch**: Custom version increments

## 🛠️ **Configuration**

### **Customizing Commit Message Patterns**

Edit `.git/hooks/pre-commit` to change the patterns:

```bash
# Example: Add custom patterns
if [[ "$COMMIT_MSG" =~ ^(hotfix|urgent) ]]; then
    INCREMENT_TYPE="patch"
elif [[ "$COMMIT_MSG" =~ ^(docs|chore) ]]; then
    INCREMENT_TYPE="none"  # No version bump
fi
```

### **Disabling Auto-increment for Specific Commits**

```bash
# Use [skip-version] in commit message
git commit -m "docs: update README [skip-version]"
```

## ⚠️ **Important Notes**

### **When Auto-increment Happens**

- ✅ **Pre-commit hook**: Every local commit
- ✅ **GitHub Actions**: Every push to main/develop
- ❌ **Direct pushes**: No auto-increment (use hooks)
- ❌ **Merge commits**: No auto-increment (use conventional commits)

### **Best Practices**

1. **Use conventional commit messages** for automatic detection
2. **Test locally** before pushing to avoid unwanted increments
3. **Review version changes** in pull requests
4. **Tag releases** after major/minor increments
5. **Keep commit history clean** for accurate versioning

## 🔍 **Troubleshooting**

### **Hook Not Working**

```bash
# Check if hook is executable
ls -la .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit

# Test the hook manually
.git/hooks/pre-commit
```

### **Version Not Incrementing**

```bash
# Check current version
python -c "from observables import __version__; print(__version__)"

# Check hook output
git commit -m "test: version increment" --dry-run

# Verify hook is active
cat .git/hooks/pre-commit
```

### **Wrong Increment Type**

```bash
# Check commit message format
git log --oneline -1

# Use explicit patterns
git commit -m "feat: new feature"  # → Minor increment
git commit -m "BREAKING CHANGE: API change"  # → Major increment
```

## 📚 **Advanced Usage**

### **Custom Version Patterns**

You can modify the version manager to support:

- **Pre-release versions**: `0.2.6-alpha.1`
- **Build metadata**: `0.2.6+build.123`
- **Custom increment rules**: Based on file changes, branch names, etc.

### **CI/CD Integration**

The version manager can be integrated with:

- **Jenkins pipelines**
- **GitLab CI**
- **Azure DevOps**
- **CircleCI**

### **Pre-commit Framework**

For more advanced Git hooks, consider using the pre-commit framework:

```bash
pip install pre-commit
pre-commit install
```

## 🎉 **Benefits**

- **Never forget** to bump versions
- **Consistent** version numbering
- **Automated** release management
- **Professional** development workflow
- **Semantic** versioning enforcement

Your project now has enterprise-grade version management! 🚀
