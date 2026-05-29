import cv2
import pygame
import numpy as np
import sys
from engine_3d import Engine3D
from hand_tracker import HandTracker

class AR3DBuilderApp:
    def __init__(self):
        pygame.init()
        self.width = 1280
        self.height = 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("AR 3D Wireframe Hologram Builder")
        self.clock = pygame.time.Clock()
        
        # Initialize modules
        self.engine = Engine3D(self.width, self.height)
        self.tracker = HandTracker()
        
        # Camera Setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.webcam_connected = self.cap.isOpened()
        
        # App state
        self.running = True
        self.cubes = []             # List of placed cubes: {"center": (x,y,z), "color": (r,g,b), "size": size}
        self.cube_size = 40         # Size of spawned cubes
        self.colors = [
            (0, 255, 255),          # Neon Cyan
            (50, 255, 100),         # Neon Green
            (255, 50, 150),         # Neon Magenta
            (255, 170, 0)           # Neon Orange
        ]
        self.active_color_idx = 0
        
        # Grid snapping
        self.grid_snap = True
        self.snap_size = 40
        
        # Cooldowns and gesture state tracking
        self.last_pinched = False
        self.last_grabbing = False
        self.grab_start_pos = None
        self.grab_start_yaw = 0
        self.grab_start_pitch = 0
        
        # Fallback simulation states (when webcam is disabled/unavailable)
        self.mouse_z = 0.0
        self.simulated_hand_pos = np.array([0.0, 0.0, 0.0])
        self.simulated_pinched = False
        self.simulated_grabbing = False
        
        # HUD Fonts
        self.font_title = pygame.font.SysFont("Consolas", 28, bold=True)
        self.font_header = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_body = pygame.font.SysFont("Consolas", 14)
        
    def check_webcam(self):
        """Periodically attempts to reconnect webcam if connection failed initially."""
        if not self.webcam_connected:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.webcam_connected = True
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def draw_hud(self, cursor_pos, active_mode):
        """Draws a gorgeous, futuristic sci-fi hologram HUD on top of the screen."""
        hud_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # --- TITLE BAR ---
        title_text = self.font_title.render("// NEON WIREFRAME AR BUILDER", True, (0, 255, 255))
        hud_surface.blit(title_text, (30, 25))
        
        # Outer boundary lines for sci-fi aesthetic
        pygame.draw.line(hud_surface, (0, 255, 255, 100), (30, 65), (500, 65), 2)
        pygame.draw.line(hud_surface, (0, 255, 255, 50), (500, 65), (self.width - 30, 65), 1)
        pygame.draw.line(hud_surface, (0, 255, 255, 100), (self.width - 30, 25), (self.width - 30, 65), 2)
        
        # --- STATE / INFO CARD (TOP RIGHT) ---
        panel_x = self.width - 320
        panel_y = 80
        panel_w = 290
        panel_h = 160
        
        # Translucent dark-cyan card background
        pygame.draw.rect(hud_surface, (5, 20, 30, 200), (panel_x, panel_y, panel_w, panel_h), border_radius=6)
        pygame.draw.rect(hud_surface, (0, 255, 255, 100), (panel_x, panel_y, panel_w, panel_h), 1, border_radius=6)
        
        # Card content
        state_title = self.font_header.render("[ SYSTEM MONITOR ]", True, (0, 255, 255))
        hud_surface.blit(state_title, (panel_x + 15, panel_y + 15))
        
        # Connection status
        cam_status = "CONNECTED (AR ON)" if self.webcam_connected else "DISCONNECTED (MOUSE SIM)"
        cam_color = (100, 255, 150) if self.webcam_connected else (255, 100, 100)
        hud_surface.blit(self.font_body.render(f"INPUT SRC: {cam_status}", True, cam_color), (panel_x + 15, panel_y + 45))
        
        # Mode
        mode_color = (0, 255, 255) if "BUILD" in active_mode else (255, 200, 50) if "CAMERA" in active_mode else (150, 150, 150)
        hud_surface.blit(self.font_body.render(f"SYS MODE : {active_mode}", True, mode_color), (panel_x + 15, panel_y + 70))
        
        # Active Color
        c_rgb = self.colors[self.active_color_idx]
        hud_surface.blit(self.font_body.render("CUBE COLOR: ", True, (240, 240, 240)), (panel_x + 15, panel_y + 95))
        pygame.draw.rect(hud_surface, c_rgb, (panel_x + 110, panel_y + 95, 30, 14), border_radius=3)
        
        # Count
        hud_surface.blit(self.font_body.render(f"ENTITIES  : {len(self.cubes)} cubes", True, (240, 240, 240)), (panel_x + 15, panel_y + 125))
        
        # --- COORDINATES CARD (BOTTOM LEFT) ---
        coord_x = 30
        coord_y = self.height - 180
        coord_w = 280
        coord_h = 150
        
        pygame.draw.rect(hud_surface, (5, 20, 30, 200), (coord_x, coord_y, coord_w, coord_h), border_radius=6)
        pygame.draw.rect(hud_surface, (0, 255, 255, 100), (coord_x, coord_y, coord_w, coord_h), 1, border_radius=6)
        
        hud_surface.blit(self.font_header.render("[ CURSOR COORDINATES ]", True, (0, 255, 255)), (coord_x + 15, coord_y + 15))
        
        if cursor_pos is not None:
            cx, cy, cz = cursor_pos
            hud_surface.blit(self.font_body.render(f"X (Horizontal): {cx:6.1f} mm", True, (220, 240, 255)), (coord_x + 15, coord_y + 45))
            hud_surface.blit(self.font_body.render(f"Y (Vertical)  : {cy:6.1f} mm", True, (220, 240, 255)), (coord_x + 15, coord_y + 70))
            hud_surface.blit(self.font_body.render(f"Z (Depth)     : {cz:6.1f} mm", True, (220, 240, 255)), (coord_x + 15, coord_y + 95))
            
            # Snap indicator
            snap_x = round(cx / self.snap_size) * self.snap_size
            snap_y = round(cy / self.snap_size) * self.snap_size
            snap_z = round(cz / self.snap_size) * self.snap_size
            hud_surface.blit(self.font_body.render(f"SNAPPED TO    : ({snap_x}, {snap_y}, {snap_z})", True, (0, 255, 255)), (coord_x + 15, coord_y + 120))
        else:
            hud_surface.blit(self.font_body.render("NO TARGET DETECTED", True, (255, 100, 100)), (coord_x + 15, coord_y + 45))
            
        # --- CONTROLS / LEGEND (BOTTOM RIGHT) ---
        leg_x = self.width - 370
        leg_y = self.height - 230
        leg_w = 340
        leg_h = 200
        
        pygame.draw.rect(hud_surface, (5, 20, 30, 200), (leg_x, leg_y, leg_w, leg_h), border_radius=6)
        pygame.draw.rect(hud_surface, (0, 255, 255, 100), (leg_x, leg_y, leg_w, leg_h), 1, border_radius=6)
        
        hud_surface.blit(self.font_header.render("[ AR CONTROL CHEATSHEET ]", True, (0, 255, 255)), (leg_x + 15, leg_y + 15))
        
        controls_list = [
            ("Pinch Index + Thumb", "Place Neon Cube"),
            ("Pinch Middle + Thumb", "Drag to Rotate Workspace"),
            ("Keys 1, 2, 3, 4", "Switch Cube Color"),
            ("Key U", "Undo Last Cube"),
            ("Key C", "Clear All Cubes"),
            ("Key Q / ESC", "Quit App"),
            ("Mouse Wheel (Simulation)", "Modify Depth (Z)")
        ]
        
        for idx, (gesture, action) in enumerate(controls_list):
            y_offset = leg_y + 45 + (idx * 20)
            # Gesture / Input
            hud_surface.blit(self.font_body.render(gesture, True, (0, 255, 255)), (leg_x + 15, y_offset))
            # Action
            hud_surface.blit(self.font_body.render(f"-> {action}", True, (240, 240, 240)), (leg_x + 180, y_offset))
            
        self.screen.blit(hud_surface, (0, 0))

    def run(self):
        """Runs the main application loop."""
        while self.running:
            active_mode = "STANDBY"
            cursor_pos = None
            
            # --- 1. HANDLE PYGAME KEYBOARD/MOUSE INPUT ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_c:
                        self.cubes.clear()
                    elif event.key == pygame.K_u:
                        if self.cubes:
                            self.cubes.pop()
                    elif event.key == pygame.K_1:
                        self.active_color_idx = 0
                    elif event.key == pygame.K_2:
                        self.active_color_idx = 1
                    elif event.key == pygame.K_3:
                        self.active_color_idx = 2
                    elif event.key == pygame.K_4:
                        self.active_color_idx = 3
                elif event.type == pygame.MOUSEWHEEL:
                    # Mouse wheel modifies depth in simulation mode
                    self.mouse_z = np.clip(self.mouse_z + event.y * 15, -200, 200)

            # --- 2. HANDLE WEBCAM STREAM & HAND TRACKING ---
            background_drawn = False
            
            if self.webcam_connected:
                ret, frame = self.cap.read()
                if ret:
                    # Mirror frame horizontally so hand moves naturally
                    frame = cv2.flip(frame, 1)
                    
                    # Run MediaPipe tracking and draw overlay on it
                    hand_info = self.tracker.process_frame(frame)
                    
                    # Darken and cyan-tint the webcam frame for an AR HUD holographic visual
                    # We process the frame before rendering it to the Pygame screen
                    # Normalizing/Tinting: BGR values multiplied to fit dark cyan palette
                    frame_tinted = cv2.multiply(frame, np.array([0.45, 0.35, 0.25])) # BGR multipliers (low red, med green, higher blue)
                    
                    # Convert to Pygame Surface
                    # OpenCV uses BGR, Pygame uses RGB. Invert channels:
                    rgb_tinted = cv2.cvtColor(frame_tinted, cv2.COLOR_BGR2RGB)
                    # Transpose to align with Pygame surface format (height, width, channels) -> (width, height, channels)
                    rgb_tinted = np.rot90(rgb_tinted)
                    webcam_surf = pygame.surfarray.make_surface(rgb_tinted)
                    webcam_surf = pygame.transform.flip(webcam_surf, True, False) # Rectify rotation flip
                    webcam_surf = pygame.transform.scale(webcam_surf, (self.width, self.height))
                    
                    self.screen.blit(webcam_surf, (0, 0))
                    background_drawn = True
                    
                    # Process hand parameters if tracking is active
                    if hand_info["cursor_3d"] is not None:
                        cursor_pos = hand_info["cursor_3d"]
                        is_pinched = hand_info["is_pinched"]
                        is_grabbing = hand_info["is_grabbing"]
                        
                        # Set active mode
                        if is_grabbing:
                            active_mode = "CAMERA ORBIT"
                        elif is_pinched:
                            active_mode = "BUILD (PLACING)"
                        else:
                            active_mode = "BUILD (MOVE)"
                            
                        # Handle Camera Manipulation (Orbit)
                        if is_grabbing:
                            if not self.last_grabbing:
                                self.grab_start_pos = cursor_pos.copy()
                                self.grab_start_yaw = self.engine.yaw
                                self.grab_start_pitch = self.engine.pitch
                                self.last_grabbing = True
                            else:
                                # Calculate gesture displacement
                                delta = cursor_pos - self.grab_start_pos
                                # Map movement in X to Yaw, Y to Pitch
                                self.engine.yaw = (self.grab_start_yaw - delta[0] * 0.4) % 360
                                self.engine.pitch = np.clip(self.grab_start_pitch + delta[1] * 0.4, -85, 85)
                        else:
                            self.last_grabbing = False
                            
                        # Handle Cube Spawning (Pinch)
                        if is_pinched:
                            if not self.last_pinched:
                                # Spawn a new cube!
                                target_pos = cursor_pos.copy()
                                if self.grid_snap:
                                    target_pos[0] = round(target_pos[0] / self.snap_size) * self.snap_size
                                    target_pos[1] = round(target_pos[1] / self.snap_size) * self.snap_size
                                    target_pos[2] = round(target_pos[2] / self.snap_size) * self.snap_size
                                    
                                self.cubes.append({
                                    "center": tuple(target_pos),
                                    "color": self.colors[self.active_color_idx],
                                    "size": self.cube_size
                                })
                                self.last_pinched = True
                        else:
                            self.last_pinched = False
                            
                else:
                    self.webcam_connected = False
            
            # --- 3. FALLBACK MOUSE SIMULATION MODE ---
            if not background_drawn:
                # Re-verify camera connection if it was lost
                self.check_webcam()
                
                # Fill screen with gorgeous dark blue cyber background
                self.screen.fill((5, 10, 18))
                
                # Render simulated grid background lines for futuristic sci-fi effect
                for y in range(0, self.height, 40):
                    pygame.draw.line(self.screen, (0, 40, 80, 20), (0, y), (self.width, y))
                for x in range(0, self.width, 40):
                    pygame.draw.line(self.screen, (0, 40, 80, 20), (x, 0), (x, self.height))
                
                # Get mouse inputs
                mx, my = pygame.mouse.get_pos()
                m_buttons = pygame.mouse.get_pressed()
                
                # Map mouse X/Y to workspace bounds
                sim_x = ((mx / self.width) - 0.5) * 450
                sim_y = (0.5 - (my / self.height)) * 400 + 50
                
                cursor_pos = np.array([sim_x, sim_y, self.mouse_z])
                
                # Simulate pinch with Left Click
                is_pinched = m_buttons[0]
                # Simulate grab with Right Click
                is_grabbing = m_buttons[2]
                
                if is_grabbing:
                    active_mode = "CAMERA ORBIT (SIM)"
                    if not self.last_grabbing:
                        self.grab_start_pos = cursor_pos.copy()
                        self.grab_start_yaw = self.engine.yaw
                        self.grab_start_pitch = self.engine.pitch
                        self.last_grabbing = True
                    else:
                        delta = cursor_pos - self.grab_start_pos
                        self.engine.yaw = (self.grab_start_yaw - delta[0] * 0.8) % 360
                        self.engine.pitch = np.clip(self.grab_start_pitch + delta[1] * 0.8, -85, 85)
                else:
                    self.last_grabbing = False
                    
                if is_pinched:
                    active_mode = "BUILD (SIM PLACING)"
                    if not self.last_pinched:
                        target_pos = cursor_pos.copy()
                        if self.grid_snap:
                            target_pos[0] = round(target_pos[0] / self.snap_size) * self.snap_size
                            target_pos[1] = round(target_pos[1] / self.snap_size) * self.snap_size
                            target_pos[2] = round(target_pos[2] / self.snap_size) * self.snap_size
                            
                        self.cubes.append({
                            "center": tuple(target_pos),
                            "color": self.colors[self.active_color_idx],
                            "size": self.cube_size
                        })
                        self.last_pinched = True
                else:
                    self.last_pinched = False
                    if not is_grabbing:
                        active_mode = "BUILD (SIM MOVE)"

            # --- 4. RENDER 3D GRID & CUBES IN PERSPECTIVE ---
            # 3D Floor Grid
            self.engine.draw_grid(self.screen)
            
            # Render already placed Cubes
            for cube in self.cubes:
                self.engine.draw_cube(
                    self.screen, 
                    cube["center"], 
                    cube["size"], 
                    cube["color"], 
                    thickness=2
                )
                
            # Render holographic cursor preview at snapped location (if hand/cursor is detected)
            if cursor_pos is not None:
                cx, cy, cz = cursor_pos
                if self.grid_snap:
                    cx = round(cx / self.snap_size) * self.snap_size
                    cy = round(cy / self.snap_size) * self.snap_size
                    cz = round(cz / self.snap_size) * self.snap_size
                
                # Active building color
                cursor_color = self.colors[self.active_color_idx]
                
                # If pinching, render active placement feedback. If standby, render transparent preview
                if active_mode.startswith("BUILD (PLACING") or active_mode.startswith("BUILD (SIM PLACING"):
                    self.engine.draw_cube(self.screen, (cx, cy, cz), self.cube_size, cursor_color, thickness=3, dotted_faces=True)
                else:
                    # Glowing preview cube (thinner lines and dots)
                    self.engine.draw_cube(self.screen, (cx, cy, cz), self.cube_size, (255, 255, 255), thickness=1, dotted_faces=True)
                    
                # Renders an interactive connector line from raw index tip position to snapped position
                raw_proj = self.engine.project_point(cursor_pos)
                snap_proj = self.engine.project_point((cx, cy, cz))
                if raw_proj and snap_proj:
                    pygame.draw.line(self.screen, (0, 255, 255, 120), raw_proj, snap_proj, 1)
                    pygame.draw.circle(self.screen, (0, 255, 255), raw_proj, 4)

            # --- 5. OVERLAY THE SCENE HUD ---
            self.draw_hud(cursor_pos, active_mode)
            
            # Update screen and maintain frame rate
            pygame.display.flip()
            self.clock.tick(60)

        # Clean shutdown
        if self.cap.isOpened():
            self.cap.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = AR3DBuilderApp()
    app.run()
