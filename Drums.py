import cv2
import numpy as np
import pygame
import math
from cvzone.HandTrackingModule import HandDetector
import time

# Initialize Pygame for sound
pygame.init()
pygame.mixer.set_num_channels(8)  # Multiple audio channels for simultaneous sounds

# Load the 3 available drum sounds
sound_files = {
    "snare": "sounds/snare.wav",
    "kick": "sounds/kick.wav",
    "hihat": "sounds/hihat.wav"
}

# Create a more realistic drum kit with the limited sounds we have
# Some drums will reuse the same samples but with different volumes
sounds = {}
for drum in sound_files:
    sounds[drum] = pygame.mixer.Sound(sound_files[drum])

# Webcam setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Hand Detector (Allow multiple hands)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# Define drum areas in a more realistic layout
# We'll reuse our 3 sounds across multiple drum pads
drum_areas = {
    "crash": (150, 200, 120, 120, "hihat", 0.8),  # (x, y, width, height, sound, volume)
    "ride": (900, 200, 120, 120, "hihat", 0.6),
    "hihat": (250, 300, 100, 100, "hihat", 1.0),
    "snare": (450, 400, 150, 150, "snare", 1.0),
    "tom1": (650, 300, 120, 120, "snare", 0.7),
    "tom2": (800, 350, 120, 120, "snare", 0.5),
    "kick": (550, 500, 200, 200, "kick", 1.0),
}

# Store last hit time for each drum to prevent multiple hits from one tap
last_hit_time = {drum: 0 for drum in drum_areas}

# Store hand position history for velocity calculation
hand_positions = {}

# Store animation states for visual feedback
animation_state = {drum: {"active": False, "start_time": 0, "duration": 0.15} for drum in drum_areas}

# Function to calculate velocity
def calculate_velocity(prev_pos, current_pos):
    if prev_pos is None:
        return 0
    dx = current_pos[0] - prev_pos[0]
    dy = current_pos[1] - prev_pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    return distance

# Function to play drum sound with velocity-based volume
def play_drum_sound(drum_info, velocity):
    sound_name = drum_info[4]  # Get sound name from drum area info
    base_volume = drum_info[5]  # Get base volume from drum area info
    
    # Scale volume based on velocity (0.3 to 1.0)
    volume_factor = min(1.0, max(0.3, velocity / 300))
    final_volume = base_volume * volume_factor
    
    # Get sound and set volume
    sound = sounds[sound_name]
    sound.set_volume(final_volume)
    
    # Play on available channel
    channel = pygame.mixer.find_channel()
    if channel:
        channel.play(sound)
    
    print(f"Hit {drum_info[4]} with volume {final_volume:.2f}")

# Main loop
while True:
    success, img = cap.read()
    if not success:
        print("Failed to get frame from camera")
        break
        
    img = cv2.flip(img, 1)  # Mirror image for more intuitive interaction
    
    # Detect hands
    hands, img = detector.findHands(img, draw=True)
    
    # Draw drum pads
    for drum, drum_info in drum_areas.items():
        x, y, w, h = drum_info[:4]
        current_time = time.time()
        is_active = animation_state[drum]["active"] and (current_time - animation_state[drum]["start_time"] < animation_state[drum]["duration"])
        
        # Draw drum pad (with animation effect if active)
        color = (200, 200, 200) if not is_active else (100, 255, 100)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
        
        # Draw drum name and sound type
        drum_name = drum.title()
        sound_name = f"({drum_info[4]})"
        
        # Position text in center of drum pad
        text_size = cv2.getTextSize(drum_name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        text_x = x + (w - text_size[0]) // 2
        cv2.putText(img, drum_name, (text_x, y + h//2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        sound_text_size = cv2.getTextSize(sound_name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        sound_text_x = x + (w - sound_text_size[0]) // 2
        cv2.putText(img, sound_name, (sound_text_x, y + h//2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    
    # Process each detected hand
    if hands:
        for hand_id, hand in enumerate(hands):
            hand_id_str = f"hand_{hand_id}"
            lmList = hand["lmList"]
            
            # Get fingertips (index, middle, ring, pinky)
            fingertips = [lmList[8][:2], lmList[12][:2], lmList[16][:2], lmList[20][:2]]
            
            # Store previous positions if they exist
            prev_positions = hand_positions.get(hand_id_str, [None, None, None, None])
            
            for i, finger_pos in enumerate(fingertips):
                x1, y1 = finger_pos
                
                # Calculate velocity
                velocity = calculate_velocity(prev_positions[i], (x1, y1))
                
                # Check if finger hits a drum pad
                for drum, drum_info in drum_areas.items():
                    x, y, w, h = drum_info[:4]
                    if x < x1 < x + w and y < y1 < y + h:
                        current_time = time.time()
                        
                        # Only trigger if velocity is significant and enough time has passed
                        if velocity > 20 and (current_time - last_hit_time[drum] > 0.2):
                            # Play sound based on velocity
                            play_drum_sound(drum_info, velocity)
                            
                            # Update last hit time
                            last_hit_time[drum] = current_time
                            
                            # Set animation state
                            animation_state[drum]["active"] = True
                            animation_state[drum]["start_time"] = current_time
            
            # Store current positions for next frame
            hand_positions[hand_id_str] = fingertips
    
    # Add instructions
    cv2.putText(img, "Virtual Drum Kit", (510, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(img, "Hit drums with fingertips - Speed = Volume", (400, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(img, "Press 'q' to quit", (550, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Display
    cv2.imshow("Virtual Drum Set", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()