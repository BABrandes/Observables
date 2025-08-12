# Troubleshooting Guide

This guide helps resolve common issues with the automatic version incrementing system.

## 🚫 **Infinite Loop Issues**

### **Problem: VS Code gets stuck in infinite commit loop**

**Symptoms:**
- VS Code shows "Running Git hooks..." indefinitely
- Multiple version increments happening
- Commit never completes

**Solutions:**

#### **Option 1: Use the Fixed Hook (Recommended)**
The current `pre-commit` hook has loop prevention built-in. If you're still experiencing issues:

```bash
# Check if the hook is working correctly
.git/hooks/pre-commit

# Verify the hook is executable
ls -la .git/hooks/pre-commit
```

#### **Option 2: Use the Enhanced Hook**
```bash
# Backup current hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.backup

# Use the enhanced version
cp .git/hooks/pre-commit-v2 .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit
```

#### **Option 3: Temporarily Disable**
```bash
# Disable the hook temporarily
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Make your commit
git add .
git commit -m "your message"

# Re-enable when ready
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

#### **Option 4: Manual Version Management**
```bash
# Disable automatic increments
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Use manual version management instead
make version-auto TYPE=patch
make version-auto TYPE=minor
make version-auto TYPE=major
```

## 🔧 **Common Issues & Solutions**

### **Issue: Hook not running**
```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit

# Test the hook manually
.git/hooks/pre-commit
```

### **Issue: Version not incrementing**
```bash
# Check current version
python -c "from observables import __version__; print(__version__)"

# Check hook output
git commit -m "test: version increment" --dry-run

# Verify hook is active
cat .git/hooks/pre-commit
```

### **Issue: Wrong increment type**
```bash
# Check commit message format
git log --oneline -1

# Use explicit patterns
git commit -m "feat: new feature"      # → Minor increment
git commit -m "BREAKING CHANGE: API"   # → Major increment
git commit -m "fix: bug"               # → Patch increment
```

### **Issue: Hook conflicts with other tools**
```bash
# Check for other pre-commit hooks
ls -la .git/hooks/

# Disable conflicting hooks temporarily
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
mv .git/hooks/pre-commit.backup .git/hooks/pre-commit
```

## 🛠️ **Advanced Troubleshooting**

### **Debug Mode**
Add debugging to the hook:

```bash
# Edit .git/hooks/pre-commit
# Add at the top:
set -x  # Enable debug mode
```

### **Check Git Configuration**
```bash
# Verify Git hooks are enabled
git config --get core.hooksPath

# Check if hooks are being skipped
git config --get core.hooksPath || echo "Using default .git/hooks"
```

### **Environment Issues**
```bash
# Check Python path in hook
which python
which python3

# Verify update_version.py is accessible
python update_version.py --help
```

## 📱 **VS Code Specific Issues**

### **VS Code Git Integration**
If VS Code is having issues:

1. **Use Terminal Instead:**
   ```bash
   # Commit from terminal instead of VS Code
   git add .
   git commit -m "your message"
   ```

2. **Disable VS Code Git Hooks:**
   - Open VS Code settings
   - Search for "git.enableCommitSigning"
   - Set to `false` temporarily

3. **Use VS Code Source Control Panel:**
   - Open Source Control panel (Ctrl+Shift+G)
   - Stage changes manually
   - Commit from there

### **VS Code Extensions**
Some VS Code extensions can interfere:

- **GitLens**: Try disabling temporarily
- **Git History**: Check settings
- **Git Graph**: Verify configuration

## 🔄 **Alternative Workflows**

### **Manual Version Management (No Hooks)**
```bash
# Disable automatic increments
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Use manual commands
make version-auto TYPE=patch
make version-auto TYPE=minor
make version-auto TYPE=major

# Commit normally
git add .
git commit -m "your message"
```

### **GitHub Actions Only**
```bash
# Disable local hooks
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Let GitHub Actions handle versioning
git push origin main
# → GitHub Actions will auto-increment versions
```

### **Pre-commit Framework**
```bash
# Install pre-commit framework
pip install pre-commit

# Create .pre-commit-config.yaml
# Configure version management there
pre-commit install
```

## 📋 **Quick Fix Checklist**

When experiencing issues:

- [ ] **Check hook exists**: `ls -la .git/hooks/pre-commit`
- [ ] **Verify executable**: `chmod +x .git/hooks/pre-commit`
- [ ] **Test manually**: `.git/hooks/pre-commit`
- [ ] **Check version files**: `cat observables/_version.py`
- [ ] **Try terminal commit**: `git commit -m "test"`
- [ ] **Disable temporarily**: `mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled`
- [ ] **Use manual versioning**: `make version-auto TYPE=patch`

## 🆘 **Getting Help**

If issues persist:

1. **Check the logs**: Look for error messages in the hook output
2. **Verify environment**: Ensure Python and Git are working correctly
3. **Try alternatives**: Use manual version management temporarily
4. **Report issues**: Include error messages and environment details

## 🎯 **Prevention Tips**

- **Test hooks locally** before pushing
- **Use conventional commits** for predictable behavior
- **Keep hooks simple** to avoid conflicts
- **Have fallback options** ready (manual versioning)
- **Document your setup** for team members

Your automatic versioning system should now be robust and loop-free! 🚀
