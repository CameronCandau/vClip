#!/usr/bin/env python3
"""
Verification script for OpIndex installation.
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")

    try:
        import yaml
        print("  ✅ PyYAML available")
    except ImportError:
        print("  ❌ PyYAML not available - install with: pip install PyYAML")
        return False

    # Check clipboard tools
    clipboard_tools = []

    # Test xclip (uses -version)
    try:
        subprocess.run(['xclip', '-version'], capture_output=True, check=True)
        clipboard_tools.append('xclip')
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Test xsel (uses --version)
    try:
        subprocess.run(['xsel', '--version'], capture_output=True, check=True)
        clipboard_tools.append('xsel')
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Test wl-copy (uses --version)
    try:
        subprocess.run(['wl-copy', '--version'], capture_output=True, check=True)
        clipboard_tools.append('wl-copy')
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    if clipboard_tools:
        print(f"  ✅ Clipboard tools available: {', '.join(clipboard_tools)}")
    else:
        print("  ⚠️  No clipboard tools found - install xclip, xsel, or wl-copy")


    # Check rofi
    try:
        subprocess.run(['rofi', '--version'], capture_output=True, check=True)
        print("  ✅ rofi available")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("  ⚠️  rofi not found - install with: sudo apt install rofi")

    return True

def test_parser():
    """Test the markdown parser."""
    print("\n📝 Testing markdown parser...")

    try:
        from cmd_manager.parser import MarkdownParser
        parser = MarkdownParser()

        # Test with sample data
        sample_file = Path("test_data/sample.md")
        if sample_file.exists():
            commands = parser.parse_file(str(sample_file))
            print(f"  ✅ Parsed {len(commands)} commands from sample.md")
        else:
            print("  ❌ Sample file not found")
            return False

    except Exception as e:
        print(f"  ❌ Parser error: {e}")
        return False

    return True

def test_config():
    """Test configuration system."""
    print("\n⚙️  Testing configuration system...")

    try:
        from cmd_manager.config import ConfigManager

        # Test config creation
        manager = ConfigManager()
        config = manager.load_config()
        print("  ✅ Configuration loaded successfully")

        # Test source file detection
        source_files = manager.get_source_files()
        print(f"  ✅ Found {len(source_files)} source files")

    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False

    return True

def test_cli():
    """Test CLI functionality."""
    print("\n🖥️  Testing CLI functionality...")

    try:
        # Test help command
        result = subprocess.run(['./opindex', '--help'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ CLI help works")
        else:
            print("  ❌ CLI help failed")
            return False

        # Test version command
        result = subprocess.run(['./opindex', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ CLI version works")
        else:
            print("  ❌ CLI version failed")
            return False

    except Exception as e:
        print(f"  ❌ CLI error: {e}")
        return False

    return True

def main():
    """Run all verification tests."""
    print("🚀 OpIndex Installation Verification")
    print("=" * 40)

    tests = [
        check_dependencies,
        test_parser,
        test_config,
        test_cli,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("\n🎉 All tests passed! OpIndex is ready to use.")
        print("\nNext steps:")
        print("1. Install dependencies if needed: pip install -r requirements.txt")
        print("2. Install rofi if needed: sudo apt install rofi")
        print("3. Install clipboard tool: sudo apt install xclip")
        print("4. Run: ./opindex --create-config")
        print("5. Add your markdown files to ~/.local/share/opindex/")
        print("6. Run: ./opindex")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
