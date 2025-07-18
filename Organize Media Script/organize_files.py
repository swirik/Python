import os
import shutil
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


month_names = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

def get_original_date(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    #  Try EXIF for JPEG images
    if ext in ['.jpg', '.jpeg']:
        try:
            image = Image.open(filepath)
            exif_data = image._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['DateTimeOriginal', 'DateTime']:
                        date_str = value.split(" ")[0].replace(":", "-")
                        return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            pass

    # Try video metadata for common formats
    if ext in ['.mp4', '.mov', '.avi', '.3gp']:
        try:
            parser = createParser(filepath)
            if parser:
                with parser:
                    metadata = extractMetadata(parser)
                    if metadata and metadata.has("creation_date"):
                        return metadata.get("creation_date")
        except Exception:
            pass

    # Fallback to file system creation date
    return datetime.fromtimestamp(os.path.getctime(filepath))

# Check if folder path is passed
if len(sys.argv) < 2:
    print("❌ Usage: python organize_files_exif_video.py <folder_path>")
    input("Press Enter to exit...")
    sys.exit(1)

base_dir = sys.argv[1]

if not os.path.exists(base_dir):
    print(f"❌ Folder does not exist: {base_dir}")
    input("Press Enter to exit...")
    sys.exit(1)

# Walk through all files
for root, dirs, files in os.walk(base_dir):
    # Skip already sorted folders like base_dir/2024/July
    rel = os.path.relpath(root, base_dir)
    parts = rel.split(os.sep)
    if len(parts) == 2 and parts[0].isdigit() and parts[1] in month_names.values():
        continue

    for file in files:
        file_path = os.path.join(root, file)

        # Skip the script itself
        if file == os.path.basename(__file__):
            continue

        try:
            date = get_original_date(file_path)
        except Exception as e:
            print(f"❌ Error reading date for {file_path}: {e}")
            continue

        if not date:
            print(f"⚠️ Could not determine date for: {file_path}")
            continue

        year = str(date.year)
        month = month_names[date.month]

        # Create folders like base_dir/2023/September
        year_folder = os.path.join(base_dir, year)
        month_folder = os.path.join(year_folder, month)
        os.makedirs(month_folder, exist_ok=True)

        # Avoid overwriting files
        destination = os.path.join(month_folder, file)
        counter = 1
        while os.path.exists(destination):
            name, ext = os.path.splitext(file)
            new_name = f"{name}_{counter}{ext}"
            destination = os.path.join(month_folder, new_name)
            counter += 1

        shutil.move(file_path, destination)
        print(f"✅ Moved: {file_path} → {destination}")

input("\n✅ Done organizing. Press Enter to close...")
