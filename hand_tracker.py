import cv2
import mediapipe as mp
import numpy as np
import math
class HandTracker:
    def __init__(self):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Depth calibration parameters
        self.depth_calibration = 22.0  # Constant factor to calibrate depth estimation
        
        # Gesture thresholds (in normalized coordinates)
        self.pinch_threshold = 0.08  # Thumb and Index finger close
        self.grab_threshold = 0.1   # Thumb and Middle finger close

    def get_distance(self, lm1, lm2):
        """Calculates Euclidean distance between two landmarks in 3D."""
        return math.sqrt(
            (lm1.x - lm2.x) ** 2 +
            (lm1.y - lm2.y) ** 2 +
            (lm1.z - lm2.z) ** 2
        )

    def process_frame(self, frame):
        """Processes a frame, extracts hand position, gesture states, and draws tracking skeleton."""
        # Convert BGR frame to RGB
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_data = {
            "landmarks": None,
            "cursor_3d": None,         # Estimated (X, Y, Z) in workspace coordinates
            "screen_cursor": None,      # (x, y) in pixels
            "is_pinched": False,        # Index + Thumb pinch
            "is_grabbing": False,       # Middle + Thumb pinch
            "pinch_distance": 0.0,
            "grab_distance": 0.0,
            "raw_landmarks": None
        }

        if results.multi_hand_landmarks:
            # We track the first hand found
            hand_landmarks = results.multi_hand_landmarks[0]
            hand_data["raw_landmarks"] = hand_landmarks
            
            # Extract key landmarks
            lms = hand_landmarks.landmark
            wrist = lms[self.mp_hands.HandLandmark.WRIST]
            knuckle = lms[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
            thumb_tip = lms[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = lms[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = lms[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            
            # --- Estimate Depth (Z) ---
            # 2D Screen distance between Wrist (0) and Middle Knuckle (9)
            dx = (wrist.x - knuckle.x) * w
            dy = (wrist.y - knuckle.y) * h
            dist_2d = math.sqrt(dx*dx + dy*dy)
            
            if dist_2d > 0:
                # Closer hand = larger dist_2d = smaller depth_z
                # Farther hand = smaller dist_2d = larger depth_z
                # We normalize it around 0 for the center of the workspace
                raw_depth = self.depth_calibration / dist_2d
                # Scale depth to workspace size (-200 to +200)
                # Calibrated baseline: distance of 80px is Z = 0
                depth_z = (raw_depth - 0.25) * 600
                depth_z = np.clip(depth_z, -200, 200)
            else:
                depth_z = 0.0

            # --- Map Coordinates to Workspace ---
            # Map index finger tip X and Y to our 3D workspace.
            # Normal camera index x is 0 (left) to 1 (right). 
            # Note: Webcam is typically mirrored, so index.x = 0.1 is right, 0.9 is left.
            # We want: 0.1 (left of user) -> -180, 0.9 (right of user) -> +180 in Pygame.
            # Wait, since the camera is mirrored, we want: x_coord = (0.5 - index_tip.x) * workspace_width
            # Let's calibrate mapping:
            # X: 0.1 to 0.9 -> -200 to 200
            # Y: 0.2 to 0.8 -> -100 to 200 (Note: camera y is 0 at top, 1 at bottom. Workspace y is + at top, - at bottom)
            # So, workspace y = (0.8 - index_tip.y) * 400 - 100
            workspace_x = (0.5 - index_tip.x) * 500  # Mirroring is corrected here!
            workspace_y = (0.75 - index_tip.y) * 450 - 100
            
            workspace_x = np.clip(workspace_x, -200, 200)
            workspace_y = np.clip(workspace_y, -100, 250)
            
            hand_data["cursor_3d"] = np.array([workspace_x, workspace_y, depth_z])
            hand_data["screen_cursor"] = (int(index_tip.x * w), int(index_tip.y * h))
            
            # --- Detect Gestures ---
            # 1. Index Pinch (spawn cubes)
            pinch_dist = self.get_distance(thumb_tip, index_tip)
            hand_data["pinch_distance"] = pinch_dist
            hand_data["is_pinched"] = pinch_dist < self.pinch_threshold
            
            # 2. Middle Pinch (grab/rotate camera)
            grab_dist = self.get_distance(thumb_tip, middle_tip)
            hand_data["grab_distance"] = grab_dist
            hand_data["is_grabbing"] = grab_dist < self.grab_threshold
            
            # Draw MediaPipe hand landmarks overlay on the BGR frame
            self.mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
            
        return hand_data
