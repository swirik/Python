import cv2
import numpy as np
import math
from cvzone.HandTrackingModule import HandDetector
import time
import os

detector = HandDetector(detectionCon=0.9, maxHands=1)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)  
cap.set(4, 720)  

canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255

colors = [
    (0, 0, 0),       
    (0, 0, 255),     
    (0, 255, 0),     
    (255, 0, 0),     
    (0, 255, 255),   
    (255, 255, 255)  
]
current_color_index = 0
current_color = colors[current_color_index]

# Adjustable brush settings
brush_thickness = 2  # Default thin line for precision
eraser_thickness = 20
min_thickness = 1
max_thickness = 10

# Grid settings
grid_enabled = True
grid_spacing = 50
grid_color = (200, 200, 200)  # Light gray

# Define color selection circles
color_circles = []
circle_radius = 20
spacing = 10
start_x = 50
y_position = 50

for i, color in enumerate(colors):
    color_circles.append((start_x + i * (2 * circle_radius + spacing), y_position, color))

# UI settings
is_drawing = False
previous_points = []  # Store multiple previous points for smoothing
menu_visible = True
menu_toggle_time = 0
clear_button = (1130, 50, 1230, 80)  # x1, y1, x2, y2
grid_button = (1130, 100, 1230, 130)
thickness_slider = (50, 100, 250, 120)  # x1, y1, x2, y2
save_button = (1130, 150, 1230, 180)

drawing_modes = ["Normal", "Straight Line", "Circle", "Square"]
current_mode = 0
mode_button = (1130, 200, 1230, 230)
start_point = None

stabilization = 0.5


def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Function to draw grid on canvas
def draw_grid(img, spacing, color):
    if grid_enabled:
        h, w = img.shape[:2]
        
        # Draw vertical lines
        for x in range(0, w, spacing):
            cv2.line(img, (x, 0), (x, h), color, 1)
        
        # Draw horizontal lines
        for y in range(0, h, spacing):
            cv2.line(img, (0, y), (w, y), color, 1)
        
        # Draw x and y axes with slightly darker color
        cv2.line(img, (w//2, 0), (w//2, h), (100, 100, 100), 2)  # Y-axis
        cv2.line(img, (0, h//2), (w, h//2), (100, 100, 100), 2)  # X-axis

# Function to get stabilized point from history
def get_stabilized_point(current_point, history):
    if not history:
        return current_point
    
    avg_x = current_point[0] * (1 - stabilization) + sum(p[0] for p in history) * stabilization / len(history)
    avg_y = current_point[1] * (1 - stabilization) + sum(p[1] for p in history) * stabilization / len(history)
    
    return (int(avg_x), int(avg_y))

# Create directory for saving images if it doesn't exist
if not os.path.exists("saved_equations"):
    os.makedirs("saved_equations")

# Main loop
while True:
    # Read frame from webcam
    success, img = cap.read()
    if not success:
        break
        
    # Flip the image horizontally for a more natural interaction
    img = cv2.flip(img, 1)
    
    # Find hands
    hands, img = detector.findHands(img, draw=True, flipType=False)
    
    # Draw grid on canvas (make a copy to preserve the original drawing)
    display_canvas = canvas.copy()
    if grid_enabled:
        draw_grid(display_canvas, grid_spacing, grid_color)
    
    # Create a combined image (original + drawing)
    combined_img = img.copy()
    
    # Add canvas with higher opacity for better visibility of math work
    combined_img = cv2.addWeighted(combined_img, 0.3, display_canvas, 0.7, 0)
    
    # Get current time for menu toggle
    current_time = time.time()
    
    # Draw menu if visible
    if menu_visible:
        # Draw color selection circles
        for center_x, center_y, color in color_circles:
            cv2.circle(combined_img, (center_x, center_y), circle_radius, color, -1)
            if color == current_color:
                cv2.circle(combined_img, (center_x, center_y), circle_radius + 5, (0, 0, 255), 2)
                
        # Draw clear button
        cv2.rectangle(combined_img, (clear_button[0], clear_button[1]), 
                     (clear_button[2], clear_button[3]), (0, 0, 255), -1)
        cv2.putText(combined_img, "Clear", (clear_button[0] + 25, clear_button[1] + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw grid toggle button
        grid_color_bg = (0, 255, 0) if grid_enabled else (100, 100, 100)
        cv2.rectangle(combined_img, (grid_button[0], grid_button[1]), 
                     (grid_button[2], grid_button[3]), grid_color_bg, -1)
        cv2.putText(combined_img, "Grid", (grid_button[0] + 35, grid_button[1] + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw thickness slider
        cv2.rectangle(combined_img, (thickness_slider[0], thickness_slider[1]), 
                     (thickness_slider[2], thickness_slider[3]), (100, 100, 100), -1)
        
        # Calculate slider position based on current thickness
        slider_pos = int(thickness_slider[0] + (brush_thickness - min_thickness) * 
                        (thickness_slider[2] - thickness_slider[0]) / (max_thickness - min_thickness))
        
        cv2.circle(combined_img, (slider_pos, (thickness_slider[1] + thickness_slider[3])//2), 
                  10, (0, 0, 255), -1)
        
        cv2.putText(combined_img, "Thickness", (thickness_slider[0], thickness_slider[1] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw save button
        cv2.rectangle(combined_img, (save_button[0], save_button[1]), 
                     (save_button[2], save_button[3]), (255, 0, 0), -1)
        cv2.putText(combined_img, "Save", (save_button[0] + 35, save_button[1] + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw mode button
        cv2.rectangle(combined_img, (mode_button[0], mode_button[1]), 
                     (mode_button[2], mode_button[3]), (0, 0, 255), -1)
        cv2.putText(combined_img, drawing_modes[current_mode], (mode_button[0] + 10, mode_button[1] + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Display instructions for calculus
        instructions = [
            "Calculus Drawing Tools:",
            "- Index finger: Move cursor",
            "- Index + Middle up: Draw",
            "- Pinch: Precision mode",
            "- Make a fist: Toggle menu",
            "- Modes: Freehand/Line/Circle/Square",
            "- Save your work with Save button"
        ]
        
        for i, line in enumerate(instructions):
            cv2.putText(combined_img, line, (800, 300 + i*30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Process hand
    if hands:
        hand = hands[0]  # Get the first hand detected
        lmList = hand["lmList"]  # List of 21 landmarks
        fingers = detector.fingersUp(hand)  # Check which fingers are up
        
        # Get index finger tip position
        index_finger_tip = lmList[8][:2]
        middle_finger_tip = lmList[12][:2]
        
        # Calculate finger distance for pinch detection (precision mode)
        finger_distance = calculate_distance(index_finger_tip, middle_finger_tip)
        is_pinching = finger_distance < 30
        
        # Use stabilization for smoother drawing
        if len(previous_points) > 5:
            previous_points.pop(0)
        previous_points.append(index_finger_tip)
        
        stabilized_point = get_stabilized_point(index_finger_tip, previous_points)
        x, y = stabilized_point
        
        # Check if making a fist to toggle menu (all fingers down)
        if sum(fingers) == 0:
            if current_time - menu_toggle_time > 1.0:  # Prevent rapid toggling
                menu_visible = not menu_visible
                menu_toggle_time = current_time
                time.sleep(0.2)  # Small delay to prevent multiple toggles
        
        # Handle menu interactions
        if menu_visible and fingers[1] == 1:  # Index finger is up
            # Check color selection
            for i, (center_x, center_y, color) in enumerate(color_circles):
                if calculate_distance((center_x, center_y), index_finger_tip) < circle_radius:
                    current_color_index = i
                    current_color = colors[current_color_index]
                    time.sleep(0.2)
            
            # Check clear button
            if (clear_button[0] < x < clear_button[2] and 
                clear_button[1] < y < clear_button[3]):
                canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255
                time.sleep(0.2)
            
            # Check grid button
            if (grid_button[0] < x < grid_button[2] and 
                grid_button[1] < y < grid_button[3]):
                grid_enabled = not grid_enabled
                time.sleep(0.2)
            
            # Check thickness slider
            if (thickness_slider[0] < x < thickness_slider[2] and 
                thickness_slider[1] - 10 < y < thickness_slider[3] + 10):
                normalized_pos = (x - thickness_slider[0]) / (thickness_slider[2] - thickness_slider[0])
                brush_thickness = int(min_thickness + normalized_pos * (max_thickness - min_thickness))
                brush_thickness = max(min_thickness, min(max_thickness, brush_thickness))
            
            # Check save button
            if (save_button[0] < x < save_button[2] and 
                save_button[1] < y < save_button[3]):
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"saved_equations/calculus_{timestamp}.png"
                cv2.imwrite(filename, canvas)
                cv2.putText(combined_img, f"Saved as {filename}", (400, 400), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                time.sleep(0.5)
            
            # Check mode button
            if (mode_button[0] < x < mode_button[2] and 
                mode_button[1] < y < mode_button[3]):
                current_mode = (current_mode + 1) % len(drawing_modes)
                start_point = None  # Reset start point when changing modes
                time.sleep(0.2)
        
        # Drawing logic based on mode and gestures
        # Normal drawing mode - index and middle fingers up
        if fingers[1] and fingers[2]:
            if current_mode == 0:  # Normal freehand drawing
                # Adjust thickness for precision if pinching
                actual_thickness = max(1, brush_thickness // 2) if is_pinching else brush_thickness
                
                # Use the eraser if white is selected
                if current_color == (255, 255, 255):
                    # Eraser (draw white with thicker line)
                    if previous_points:
                        for i in range(1, len(previous_points)):
                            pt1 = previous_points[i-1]
                            pt2 = previous_points[i]
                            cv2.line(canvas, pt1, pt2, current_color, eraser_thickness)
                else:
                    # Normal drawing
                    if len(previous_points) > 1:
                        for i in range(1, len(previous_points)):
                            pt1 = previous_points[i-1]
                            pt2 = previous_points[i]
                            cv2.line(canvas, pt1, pt2, current_color, actual_thickness)
            
            elif current_mode == 1:  
                if start_point is None:
                    start_point = stabilized_point
                else:
                    # Draw a dynamic preview line on the combined image
                    cv2.line(combined_img, start_point, stabilized_point, current_color, brush_thickness)
                    
                    # Check if fingers are pinched to finalize the line
                    if is_pinching:
                        cv2.line(canvas, start_point, stabilized_point, current_color, brush_thickness)
                        start_point = None  # Reset for a new line
                        time.sleep(0.2)
            
            elif current_mode == 2:  # Circle mode
                if start_point is None:
                    start_point = stabilized_point
                else:
                    # Calculate radius
                    radius = int(calculate_distance(start_point, stabilized_point))
                    
                    # Draw a dynamic preview circle on the combined image
                    cv2.circle(combined_img, start_point, radius, current_color, brush_thickness)
                    
                    # Check if fingers are pinched to finalize the circle
                    if is_pinching:
                        cv2.circle(canvas, start_point, radius, current_color, brush_thickness)
                        start_point = None  # Reset for a new circle
                        time.sleep(0.2)
            
            elif current_mode == 3:  # Square/Rectangle mode
                if start_point is None:
                    start_point = stabilized_point
                else:
                    # Draw a dynamic preview rectangle on the combined image
                    cv2.rectangle(combined_img, start_point, stabilized_point, current_color, brush_thickness)
                    
                    # Check if fingers are pinched to finalize the rectangle
                    if is_pinching:
                        cv2.rectangle(canvas, start_point, stabilized_point, current_color, brush_thickness)
                        start_point = None  # Reset for a new rectangle
                        time.sleep(0.2)
        
        # Moving without drawing (only index finger up)
        elif fingers[1] and not fingers[2]:
            # Just update the cursor position
            start_point = None  # Reset shape start points when moving
            
            # Draw the cursor position as a small circle
            cursor_size = 5 if is_pinching else 10  # Smaller cursor for precision mode
            cv2.circle(combined_img, stabilized_point, cursor_size, current_color, -1)
        
        # Reset when no drawing fingers are up
        else:
            start_point = None
    
    # Add a status bar with info for calculus
    cv2.rectangle(combined_img, (0, 0), (1280, 30), (50, 50, 50), -1)
    
    # Show current mode and color in status bar
    mode_text = f"Mode: {drawing_modes[current_mode]}"
    cv2.putText(combined_img, mode_text, (10, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Show current color
    cv2.putText(combined_img, "Color:", (200, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.circle(combined_img, (260, 15), 10, current_color, -1)
    
    # Show current thickness
    thickness_text = f"Thickness: {brush_thickness}"
    cv2.putText(combined_img, thickness_text, (300, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Show grid status
    grid_text = "Grid: On" if grid_enabled else "Grid: Off"
    cv2.putText(combined_img, grid_text, (450, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Menu status
    menu_text = "Menu: On" if menu_visible else "Menu: Off (make fist to show)"
    cv2.putText(combined_img, menu_text, (550, 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Show the combined image
    cv2.imshow("Calculus Drawing Tool", combined_img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()