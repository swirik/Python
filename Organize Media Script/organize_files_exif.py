import os
import shutil
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS


month_names = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def get_original_date(filepath):
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    date_str = value.split(" ")[0].replace(":", "-")
                    return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        pass


    return datetime.fromtimestamp(os.path.getctime(filepath))


if len(sys.argv) < 2:
    print("❌ Usage: python organize_by_year_and_month_exif.py <folder_path>")
    sys.exit(1)

base_dir = sys.argv[1]

if not os.path.exists(base_dir):
    print(f"❌ Folder does not exist: {base_dir}")
    sys.exit(1)


for root, dirs, files in os.walk(base_dir):

    rel = os.path.relpath(root, base_dir)
    parts = rel.split(os.sep)
    if len(parts) == 2 and parts[0].isdigit() and parts[1] in month_names.values():
        continue

    for file in files:
        file_path = os.path.join(root, file)


        if file == os.path.basename(__file__):
            continue


        try:
            date = get_original_date(file_path)
        except Exception as e:
            print(f"❌ Error reading date for {file_path}: {e}")
            continue

        year = str(date.year)
        month = month_names[date.month]

        # Create folders
        year_folder = os.path.join(base_dir, year)
        month_folder = os.path.join(year_folder, month)
        os.makedirs(month_folder, exist_ok=True)


        destination = os.path.join(month_folder, file)
        counter = 1
        while os.path.exists(destination):
            name, ext = os.path.splitext(file)
            new_name = f"{name}_{counter}{ext}"
            destination = os.path.join(month_folder, new_name)
            counter += 1

        shutil.move(file_path, destination)
        print(f"✅ Moved: {file_path} → {destination}")
