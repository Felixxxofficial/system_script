import cv2
import numpy as np

# Load the input video
input_video_path = r"C:\Users\felix\Downloads\Professional_Mode_Girl_raises_the_drink_to_her_lip.mp4"  # Replace with your video file path
output_video_path = r"C:\Users\felix\Downloads\python.mp4"  # Out

cap = cv2.VideoCapture(input_video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# Subtle sharpening kernel (less aggressive than before)
sharpen_kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]], dtype=np.float32)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # End of video

    # Step 1: Adjust brightness and contrast (more subtle)
    alpha = 1.1  # Slight contrast boost
    beta = 5     # Slight brightness increase
    adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Step 2: Apply subtle sharpening
    sharpened = cv2.filter2D(adjusted, -1, sharpen_kernel)

    # Step 3: Simulate slight motion blur (very light)
    blur_kernel = np.ones((2, 2), np.float32) / 4  # Tiny blur kernel
    smoothed = cv2.filter2D(sharpened, -1, blur_kernel)

    # Step 4: Basic color correction (reduce synthetic look)
    # Slightly boost blue channel to mimic natural camera tone
    b, g, r = cv2.split(smoothed)
    b = cv2.add(b, 5)  # Add a touch of blue
    final_frame = cv2.merge((b, g, r))

    # Ensure pixel values stay within valid range (0-255)
    final_frame = np.clip(final_frame, 0, 255).astype(np.uint8)

    # Write the processed frame to the output video
    out.write(final_frame)

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"Video processing complete! Saved as {output_video_path}")

