# Version Management Guide

This document explains how to manage version numbers across the Observables project.

## 🎯 **Overview**

The project uses a **single source of truth** approach for version management:
- **Primary source**: `observables/_version.py`
- **Automatically updated**: `observables/__init__.py`, `setup.py`
- **Build system**: `pyproject.toml` (when using setuptools-scm)

## 🔧 **Methods to Update Versions**

### **Method 1: Using the Update Script (Recommended)**

```bash
# Update to a specific version
python update_version.py 0.2.6

# Or use the Makefile
make version VERSION=0.2.6
```

### **Method 2: Using setuptools-scm (Git-based)**

```bash
# Install setuptools-scm
pip install setuptools-scm[toml]

# Create and push a git tag
git tag v0.2.6
git push origin v0.2.6

# The version will be automatically derived from git tags
```

### **Method 3: Manual Update**

```bash
# Edit observables/_version.py
# Update both __version__ and __version_tuple__
# Run the update script to sync other files
python update_version.py 0.2.6
```

## 📁 **Files Updated Automatically**

When you run the version update script, these files are automatically updated:

1. **`observables/_version.py`** - Primary version source
   - `__version__ = "0.2.6"`
   - `__version_tuple__ = (0, 2, 6)`

2. **`observables/__init__.py`** - Package metadata
   - Fallback version (when _version.py is not available)
   - Version tuple fallback

3. **`setup.py`** - Build configuration
   - Fallback version for setuptools

## 🚀 **Workflow for New Releases**

### **1. Update Version**
```bash
make version VERSION=0.2.6
```

### **2. Verify Changes**
```bash
# Check that all files were updated
git diff

# Run tests to ensure nothing broke
make test
```

### **3. Commit and Tag**
```bash
git add .
git commit -m "Bump version to 0.2.6"
git tag v0.2.6
git push origin main
git push origin v0.2.6
```

### **4. Build and Publish (if applicable)**
```bash
make build
make publish
```

## 🔍 **Verification**

After updating versions, verify these files contain the correct version:

- ✅ `observables/_version.py`
- ✅ `observables/__init__.py` (fallback values)
- ✅ `setup.py` (fallback value)

## 🛠️ **Troubleshooting**

### **Version Not Updating in Some Files**
- Run `python update_version.py <version>` again
- Check file permissions
- Ensure the regex patterns in the script match your file content

### **Import Errors**
- Make sure `observables/_version.py` is included in package data
- Check that the import path in `__init__.py` is correct

### **Build Issues**
- Verify `pyproject.toml` has the correct package data configuration
- Check that `setup.py` includes `_version.py` in package data

## 📋 **Best Practices**

1. **Always use the update script** instead of manually editing files
2. **Test after version updates** to ensure nothing broke
3. **Use semantic versioning** (MAJOR.MINOR.PATCH)
4. **Commit version changes** before creating git tags
5. **Keep git tags in sync** with your version numbers

## 🔗 **Related Files**

- `update_version.py` - Version synchronization script
- `Makefile` - Contains `make version` command
- `pyproject.toml` - Build system configuration
- `setup.py` - Fallback build configuration
- `observables/_version.py` - Primary version source
- `observables/__init__.py` - Package metadata

## 📚 **Advanced Usage**

### **Custom Version Patterns**
You can modify `update_version.py` to handle custom version formats or additional files.

### **CI/CD Integration**
The version script can be integrated into CI/CD pipelines for automated version management.

### **Pre-commit Hooks**
Consider adding version checks to pre-commit hooks to ensure consistency.
