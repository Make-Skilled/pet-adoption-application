#!/usr/bin/env python3

import os
from PIL import Image

# Test if we can write to the uploads directory
uploads_dir = "static/uploads/pets"

print(f"🐾 Testing file write permissions to: {uploads_dir}")

# Check if directory exists
if not os.path.exists(uploads_dir):
    print(f"❌ Directory doesn't exist: {uploads_dir}")
    try:
        os.makedirs(uploads_dir, exist_ok=True)
        print(f"✅ Created directory: {uploads_dir}")
    except Exception as e:
        print(f"❌ Failed to create directory: {e}")
        exit(1)

# Test writing a file
try:
    test_file_path = os.path.join(uploads_dir, "test_write.txt")
    with open(test_file_path, "w") as f:
        f.write("Test file write")
    print(f"✅ Successfully wrote test file: {test_file_path}")
    
    # Clean up
    os.remove(test_file_path)
    print(f"✅ Successfully removed test file")
    
except Exception as e:
    print(f"❌ Failed to write test file: {e}")

# Test creating and saving an image
try:
    img = Image.new('RGB', (100, 100), color='blue')
    test_img_path = os.path.join(uploads_dir, "test_image.jpg")
    img.save(test_img_path)
    print(f"✅ Successfully saved test image: {test_img_path}")
    
    # Check if file exists and has content
    if os.path.exists(test_img_path):
        file_size = os.path.getsize(test_img_path)
        print(f"✅ Test image file size: {file_size} bytes")
        
        # Clean up
        os.remove(test_img_path)
        print(f"✅ Successfully removed test image")
    else:
        print(f"❌ Test image file was not created")
        
except Exception as e:
    print(f"❌ Failed to create/save test image: {e}")

print(f"🐾 File write test completed!")
