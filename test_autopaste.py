#!/usr/bin/env python3
"""
Quick test for auto-paste functionality.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from cmd_manager.clipboard import ClipboardManager
from cmd_manager.parser import Command

def test_autopaste():
    """Test auto-paste functionality."""
    print("🧪 Testing Auto-Paste Functionality")
    print("=" * 40)

    # Create a test command
    test_command = Command(
        content="echo 'Hello from vclip auto-paste!'",
        description="Test auto-paste command",
        tags=["test"],
        category="Testing",
        source_file="test",
        line_number=1
    )

    clipboard = ClipboardManager()

    # Check if clipboard tools are available
    print("📋 Checking clipboard availability...")
    if not clipboard.check_clipboard_availability():
        print("❌ No clipboard tools available!")
        return False
    print("✅ Clipboard tools found")

    # Test copying first
    print("\n📝 Testing regular copy...")
    success = clipboard.copy_command(test_command)
    if success:
        print("✅ Copy successful")
    else:
        print("❌ Copy failed")
        return False

    print("\n🚀 Testing auto-paste in 3 seconds...")
    print("   Switch to a terminal window now!")

    import time
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    # Test auto-paste
    print("\n⚡ Attempting auto-paste...")
    success = clipboard.copy_and_paste_command(test_command)

    if success:
        print("✅ Auto-paste completed!")
        print("\n🎉 If you see the command in your terminal, auto-paste works!")
    else:
        print("❌ Auto-paste failed")
        print("   This might be normal if auto-paste tools aren't installed")
        print("   Try installing: sudo apt install xdotool  # or wtype for Wayland")

    return success

if __name__ == "__main__":
    test_autopaste()