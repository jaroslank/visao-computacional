import cv2
import numpy as np
import os

def generate_hangman_assets():
    # Setup directory relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "assets", "hangman")
    os.makedirs(out_dir, exist_ok=True)
    
    width = 250
    height = 300
    color = (255, 255, 255, 255) # Solid white with full alpha transparency
    thickness = 6
    
    def create_base():
        # Create an entirely transparent base image (BGRA)
        return np.zeros((height, width, 4), dtype=np.uint8)

    def draw_gallows(img):
        # Base horizontal
        cv2.line(img, (30, 270), (130, 270), color, thickness)
        # Vertical pole
        cv2.line(img, (80, 270), (80, 30), color, thickness)
        # Top horizontal pole
        cv2.line(img, (80, 30), (180, 30), color, thickness)
        # Rope
        cv2.line(img, (180, 30), (180, 60), color, thickness)

    for stage in range(7):
        img = create_base()
        draw_gallows(img) # Draw the gallows for all stages
        
        # Sequentially draw body parts for each stage
        if stage >= 1: # Head
            cv2.circle(img, (180, 85), 25, color, thickness)
        if stage >= 2: # Body
            cv2.line(img, (180, 110), (180, 190), color, thickness)
        if stage >= 3: # Left Arm
            cv2.line(img, (180, 130), (140, 170), color, thickness)
        if stage >= 4: # Right Arm
            cv2.line(img, (180, 130), (220, 170), color, thickness)
        if stage >= 5: # Left Leg
            cv2.line(img, (180, 190), (140, 250), color, thickness)
        if stage >= 6: # Right Leg
            cv2.line(img, (180, 190), (220, 250), color, thickness)
            
        filename = os.path.join(out_dir, f"{stage}.png")
        cv2.imwrite(filename, img)
        print(f"Generated {filename}")

if __name__ == "__main__":
    generate_hangman_assets()
