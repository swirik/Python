\# 🗂️ Organize Files by Year and Month (with EXIF Support)



This Python script automatically organizes your photos and videos into folders by \*\*year and month\*\* using the file's original date.



📸 For image files (`.jpg`, `.jpeg`), it reads the \*\*EXIF metadata\*\* (Date Taken).  

🗂 For other files (like `.mp4`), it falls back to the file \*\*creation date\*\*.



---



\## ✅ Features



\- Organizes into folders like:



YourFolder/

├── 2022/

│ ├── March/

├── 2023/

│ ├── November/

├── 2024/

│ ├── July/



\- Works recursively (includes files from subfolders)

\- Automatically creates folders

\- Skips already-organized folders

\- Avoids overwriting by renaming duplicate filenames

\- Supports drag-and-drop or manual folder path input

\- Optional pause (`Press Enter to close...`) for `.exe` use



---



\## 📦 Requirements



\- Python installed  

\- Pillow library (used for reading image metadata)



\### 📥 Install Pillow



Run this in Command Prompt or terminal:

```bash

pip install pillow



