import cv2
import numpy as np
from PIL import Image
import os
import argparse
import platform
import subprocess

def convert_to_dotted_hands(input_image_path, output_path=None, dot_spacing=6, 
                           background_color=(0, 0, 0), 
                           max_dot_color=(255, 255, 255), min_dot_color=(100, 100, 100),
                           max_dot_size=2, min_dot_size=1,
                           threshold_value=30, screen_fit=True, screen_size=None):
    """
    Convert an image to a dotted representation with hands effect.
    
    Args:
        input_image_path (str): Path to the input image
        output_path (str): Path to save the output image
        dot_spacing (int): Spacing between dots in pixels
        background_color (tuple): RGB color for the background
        max_dot_color (tuple): RGB color for the brightest dots
        min_dot_color (tuple): RGB color for the dimmest dots
        max_dot_size (int): Maximum radius of dots
        min_dot_size (int): Minimum radius of dots
        threshold_value (int): Minimum brightness threshold to draw a dot (0-255)
        screen_fit (bool): Whether to resize the image to fit the screen
        screen_size (tuple): Screen dimensions (width, height)
        
    Returns:
        PIL.Image: The dotted image
        str: Path where the image is saved
    """
    # Load the input image
    input_image = Image.open(input_image_path)
    
    # Set target dimensions
    if screen_fit:
        if screen_size:
            screen_width, screen_height = screen_size
        else:
            # Default resolution
            screen_width, screen_height = 1920, 1080
            
        # Create a new background image
        dotted_image = Image.new('RGB', (screen_width, screen_height), background_color)
        
        # Resize input image to fit screen while maintaining aspect ratio
        width_ratio = screen_width / input_image.width
        height_ratio = screen_height / input_image.height
        ratio = min(width_ratio, height_ratio) * 0.999999999  # Use 80% of screen
        
        new_width = int(input_image.width * ratio)
        new_height = int(input_image.height * ratio)
        resized_image = input_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Calculate position to center the image
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2
    else:
        # Use original image dimensions
        resized_image = input_image
        dotted_image = Image.new('RGB', input_image.size, background_color)
        x_offset, y_offset = 0, 0
    
    # Convert to numpy array for processing
    img_array = np.array(resized_image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray_img = img_array
    
    # Apply some preprocessing to enhance hand detection
    # Apply adaptive thresholding to better isolate the hands
    adaptive_thresh = cv2.adaptiveThreshold(
        gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 21, 2)
    
    # Find contours to identify the hand regions
    contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a mask for the hands
    hand_mask = np.zeros_like(gray_img)
    
    # Fill the largest contours (hands) - take up to 2 largest contours
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for contour in sorted_contours[:2]:  # Focus on up to two largest contours (likely the hands)
        if cv2.contourArea(contour) > 1000:  # Minimum area to be considered a hand
            cv2.drawContours(hand_mask, [contour], -1, 255, -1)
    
    # Apply Gaussian blur to the mask to soften the edges
    hand_mask = cv2.GaussianBlur(hand_mask, (15, 15), 0)
    
    # Normalize the mask to range 0-255
    _, hand_mask = cv2.threshold(hand_mask, 1, 255, cv2.THRESH_BINARY)
    
    # Use grayscale for determining dot intensity within masked regions
    enhanced_img = cv2.convertScaleAbs(gray_img, alpha=1.2, beta=10)  # Enhance contrast
    
    # Convert back to PIL image for drawing
    draw_image = np.array(dotted_image)
    
    # Create dots based on the hand mask and processed image
    for y in range(0, resized_image.height, dot_spacing):
        for x in range(0, resized_image.width, dot_spacing):
            if y < resized_image.height and x < resized_image.width:
                # Check if this pixel is part of a hand (mask > 0)
                if hand_mask[y, x] > 0:
                    # Get brightness from the enhanced image
                    brightness = enhanced_img[y, x]
                    
                    # Only draw a dot if brightness is above threshold
                    if brightness > threshold_value:
                        # Scale dot size based on brightness
                        brightness_ratio = brightness / 255.0
                        dot_size = min_dot_size + brightness_ratio * (max_dot_size - min_dot_size)
                        
                        # Generate dot color based on brightness
                        dot_color = tuple(int(min_col + brightness_ratio * (max_col - min_col)) 
                                         for min_col, max_col in zip(min_dot_color, max_dot_color))
                        
                        # Draw the dot
                        cv2.circle(draw_image, (x + x_offset, y + y_offset), 
                                  int(dot_size), dot_color, -1)
    
    result_image = Image.fromarray(draw_image)
    
    # Save the result
    if output_path is None:
        output_dir = os.path.dirname(input_image_path)
        output_path = os.path.join(output_dir, "dotted_hands_" + os.path.basename(input_image_path))
    
    result_image.save(output_path)
    
    return result_image, output_path

def set_as_wallpaper(image_path):
    """Set an image as the desktop wallpaper."""
    system = platform.system()
    
    try:
        if system == "Windows":
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            return True
        elif system == "Darwin":  # macOS
            script = f'''tell application "System Events"
                            set desktop picture to POSIX file "{image_path}"
                        end tell'''
            subprocess.run(['osascript', '-e', script], check=True)
            return True
        elif system == "Linux":
            # This works for GNOME
            try:
                subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 
                               'picture-uri', f'file://{image_path}'], check=True)
                return True
            except subprocess.CalledProcessError:
                # Try alternate method for KDE
                try:
                    subprocess.run(['plasma-apply-wallpaperimage', image_path], check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    return False
    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        return False
    
    return False

def get_screen_resolution():
    """Attempt to get the screen resolution."""
    system = platform.system()
    
    try:
        if system == "Windows":
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            return (width, height)
        elif system == "Darwin":  # macOS
            cmd = "system_profiler SPDisplaysDataType | grep Resolution"
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            if result:
                # Parse the resolution from output like "Resolution: 2560 x 1440"
                parts = result.strip().split(": ")[1].split(" x ")
                return (int(parts[0]), int(parts[1]))
        elif system == "Linux":
            try:
                cmd = "xrandr | grep '*' | awk '{print $1}'"
                result = subprocess.check_output(cmd, shell=True).decode('utf-8')
                if result:
                    parts = result.strip().split("x")
                    return (int(parts[0]), int(parts[1]))
            except:
                pass
    except Exception as e:
        print(f"Error getting screen resolution: {e}")
    
    # Default to 1080p if we can't detect
    return (1920, 1080)

def main():
    parser = argparse.ArgumentParser(description='Convert an image to a dotted hands style')
    parser.add_argument('input_image', help='Path to the input image')
    parser.add_argument('--output', '-o', help='Path to save the output image')
    parser.add_argument('--spacing', '-s', type=int, default=6, help='Spacing between dots (default: 6)')
    parser.add_argument('--max-dot-size', '-mds', type=int, default=2, help='Maximum dot size (default: 2)')
    parser.add_argument('--min-dot-size', '-nds', type=int, default=1, help='Minimum dot size (default: 1)')
    parser.add_argument('--max-brightness', '-mb', type=int, default=255, help='Maximum dot brightness (0-255, default: 255)')
    parser.add_argument('--min-brightness', '-nb', type=int, default=100, help='Minimum dot brightness (0-255, default: 100)')
    parser.add_argument('--threshold', '-t', type=int, default=30, help='Minimum brightness to draw a dot (default: 30)')
    parser.add_argument('--no-fit', action='store_true', help='Do not resize to fit screen')
    parser.add_argument('--wallpaper', '-w', action='store_true', help='Set as wallpaper after creating')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_image):
        print(f"Error: The file {args.input_image} does not exist.")
        return
    
    print("Converting to dotted hands style...")
    
    # Get screen resolution if needed
    screen_size = None if args.no_fit else get_screen_resolution()
    
    # Calculate dot colors based on brightness settings
    max_brightness = args.max_brightness
    min_brightness = args.min_brightness
    max_dot_color = (max_brightness, max_brightness, max_brightness)
    min_dot_color = (min_brightness, min_brightness, min_brightness)
    
    # Convert image to dotted style
    dotted_image, output_path = convert_to_dotted_hands(
        args.input_image,
        output_path=args.output,
        dot_spacing=args.spacing,
        background_color=(0, 0, 0),  # Pure black background
        max_dot_color=max_dot_color,  # Brightest dots
        min_dot_color=min_dot_color,  # Dimmest dots
        max_dot_size=args.max_dot_size,
        min_dot_size=args.min_dot_size,
        threshold_value=args.threshold,
        screen_fit=not args.no_fit,
        screen_size=screen_size
    )
    
    print(f"Image saved to: {output_path}")
    
    # Set as wallpaper if requested
    if args.wallpaper:
        print("Setting as wallpaper...")
        if set_as_wallpaper(output_path):
            print("Successfully set as wallpaper!")
        else:
            print(f"Could not set as wallpaper automatically. The image is saved at: {output_path}")
    
    # Show the image
    dotted_image.show()

if __name__ == "__main__":
    # If no command line arguments are provided, use a simplified interface
    import sys
    if len(sys.argv) == 1:
        from tkinter import Tk, filedialog, simpledialog
        import tkinter.messagebox as messagebox
        
        root = Tk()
        root.withdraw()  # Hide the main window
        
        # Ask user to select input image
        input_path = filedialog.askopenfilename(
            title="Select an image with hands to convert",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if not input_path:
            print("No image selected. Exiting.")
            sys.exit(0)
            
        # Use simplified settings focused on hands
        print(f"Converting {input_path} to dotted hands style...")
        dotted_image, output_path = convert_to_dotted_hands(
            input_path,
            dot_spacing=6,
            background_color=(0, 0, 0),
            max_dot_color=(255, 255, 255),  # White for brightest areas
            min_dot_color=(100, 100, 100),  # Gray for darker areas
            max_dot_size=2,
            min_dot_size=1,
            threshold_value=30
        )
        
        # Show result and ask if user wants to set as wallpaper
        dotted_image.show()
        
        if messagebox.askyesno("Set as Wallpaper", 
                              "Would you like to set this image as your desktop wallpaper?"):
            if set_as_wallpaper(output_path):
                messagebox.showinfo("Success", f"Wallpaper set successfully!\nImage saved to: {output_path}")
            else:
                messagebox.showwarning("Warning", 
                                      f"Could not set as wallpaper automatically.\nImage saved to: {output_path}")
        else:
            messagebox.showinfo("Complete", f"Image saved to: {output_path}")
    else:
        main()