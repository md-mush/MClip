#!/usr/bin/env python3
"""
Fix ImageMagick Security Policy for MoviePy
This script fixes the ImageMagick policy that blocks MoviePy from creating text clips
"""

import os
import subprocess
import sys

def fix_imagemagick_policy():
    """Fix ImageMagick security policy to allow MoviePy operations."""
    
    policy_paths = [
        "/etc/ImageMagick-6/policy.xml",
        "/etc/ImageMagick-7/policy.xml",
        "/etc/ImageMagick/policy.xml"
    ]
    
    fixed = False
    
    for policy_file in policy_paths:
        if not os.path.exists(policy_file):
            continue
            
        print(f"📝 Found ImageMagick policy: {policy_file}")
        
        try:
            # Backup original
            backup_file = f"{policy_file}.backup"
            if not os.path.exists(backup_file):
                subprocess.run(f"cp {policy_file} {backup_file}", shell=True, check=True)
                print(f"✅ Backed up to: {backup_file}")
            
            # Read current policy
            with open(policy_file, 'r') as f:
                content = f.read()
            
            # Check if already fixed
            if 'rights="read|write" pattern="@*"' in content:
                print(f"✅ Policy already fixed: {policy_file}")
                fixed = True
                continue
            
            # Apply fixes
            original_content = content
            
            # Fix @* pattern (the main issue)
            content = content.replace(
                'rights="none" pattern="@*"',
                'rights="read|write" pattern="@*"'
            )
            content = content.replace(
                '<policy domain="path" rights="none" pattern="@\\*"',
                '<policy domain="path" rights="read|write" pattern="@*"'
            )
            
            # Also fix LABEL, TEXT, and other coders that MoviePy uses
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="LABEL"',
                '<policy domain="coder" rights="read|write" pattern="LABEL"'
            )
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="TEXT"',
                '<policy domain="coder" rights="read|write" pattern="TEXT"'
            )
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="PNG"',
                '<policy domain="coder" rights="read|write" pattern="PNG"'
            )
            
            if content != original_content:
                # Write back
                with open(policy_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Fixed ImageMagick policy: {policy_file}")
                print("   - Enabled @* pattern (temp file access)")
                print("   - Enabled LABEL coder (text rendering)")
                print("   - Enabled TEXT coder (text rendering)")
                print("   - Enabled PNG coder (image output)")
                fixed = True
            else:
                print(f"⚠️  No changes needed for: {policy_file}")
                
        except PermissionError:
            print(f"❌ Permission denied. Run with sudo:")
            print(f"   sudo python3 {__file__}")
            return False
        except Exception as e:
            print(f"❌ Error fixing policy: {e}")
            # Try using sed as fallback
            try:
                print("🔧 Trying sed fallback...")
                subprocess.run(
                    f'sed -i \'s/rights="none" pattern="@\\*"/rights="read|write" pattern="@*"/g\' {policy_file}',
                    shell=True,
                    check=True
                )
                subprocess.run(
                    f'sed -i \'s/<policy domain="coder" rights="none" pattern="LABEL"/<policy domain="coder" rights="read|write" pattern="LABEL"/g\' {policy_file}',
                    shell=True,
                    check=True
                )
                print(f"✅ Fixed using sed: {policy_file}")
                fixed = True
            except Exception as e2:
                print(f"❌ Sed fallback also failed: {e2}")
    
    if not fixed:
        print("❌ No ImageMagick policy files found or could not fix them")
        print("   Searched in:")
        for path in policy_paths:
            print(f"   - {path}")
        return False
    
    # Test the fix
    print("\n🧪 Testing ImageMagick with MoviePy...")
    try:
        import moviepy.editor as mp
        clip = mp.TextClip("Test", fontsize=24, color="white")
        print(f"✅ SUCCESS! MoviePy TextClip works! Size: {clip.size}")
        clip.close()
        return True
    except Exception as e:
        print(f"⚠️  MoviePy test failed: {e}")
        print("   The policy was fixed, but MoviePy still has issues.")
        print("   This might be due to missing fonts or other dependencies.")
        return False

def main():
    print("🚀 ImageMagick Policy Fixer for MoviePy")
    print("=" * 50)
    
    # Check if ImageMagick is installed
    try:
        result = subprocess.run("convert -version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ ImageMagick found: {version_line}")
        else:
            print("❌ ImageMagick not found. Please install it first:")
            print("   apt-get install -y imagemagick")
            return
    except Exception as e:
        print(f"❌ Could not check ImageMagick: {e}")
        return
    
    # Fix the policy
    success = fix_imagemagick_policy()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ImageMagick policy fixed successfully!")
        print("   MoviePy should now be able to create text clips.")
    else:
        print("⚠️  Policy fix completed with warnings.")
        print("   Check the messages above for details.")
    
    print("\n💡 If you still have issues, try:")
    print("   1. Restart your Python kernel/runtime")
    print("   2. Check that fonts are installed: fc-list")
    print("   3. Try using method='caption' in TextClip")

if __name__ == "__main__":
    main()
