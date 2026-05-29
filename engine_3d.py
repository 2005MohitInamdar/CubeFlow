import numpy as np
import pygame

class Engine3D:
    def __init__(self, screen_width=1280, screen_height=720):
        self.width = screen_width
        self.height = screen_height
        
        # Camera attributes
        self.camera_z = 600  # Camera distance from origin
        self.yaw = 30        # Rotation around Y axis (degrees)
        self.pitch = -25     # Rotation around X axis (degrees)
        self.focal_length = 800
        
        # Space boundaries
        self.grid_size = 400
        self.grid_divisions = 10
        self.grid_y = -100   # Y position of the floor grid
        
    def rotate_x(self, point, angle_deg):
        rad = np.radians(angle_deg)
        c, s = np.cos(rad), np.sin(rad)
        x, y, z = point
        return np.array([x, y * c - z * s, y * s + z * c])
        
    def rotate_y(self, point, angle_deg):
        rad = np.radians(angle_deg)
        c, s = np.cos(rad), np.sin(rad)
        x, y, z = point
        return np.array([x * c + z * s, y, -x * s + z * c])

    def project_point(self, point):
        """Projects a 3D point (x, y, z) to 2D screen coordinates."""
        # 1. Apply rotations (world space to camera space orientation)
        p = self.rotate_y(point, self.yaw)
        p = self.rotate_x(p, self.pitch)
        
        x, y, z = p
        
        # Translate based on camera distance
        z_cam = z + self.camera_z
        
        # Prevent division by zero / rendering behind camera
        if z_cam < 20:
            return None
            
        # 2. Perspective Projection
        screen_x = int(self.width / 2 + (x * self.focal_length) / z_cam)
        screen_y = int(self.height / 2 - (y * self.focal_length) / z_cam)
        
        return (screen_x, screen_y)

    def draw_line_3d(self, surface, pt1, pt2, color, thickness=1):
        """Draws a line in 3D space between two points."""
        proj1 = self.project_point(pt1)
        proj2 = self.project_point(pt2)
        
        if proj1 and proj2:
            pygame.draw.line(surface, color, proj1, proj2, thickness)

    def draw_grid(self, surface):
        """Renders an interactive base grid in the 3D space."""
        grid_color = (0, 140, 200, 100) # Glowing cyan/blue
        axis_color_x = (230, 70, 70)     # Red for X-axis
        axis_color_z = (70, 70, 230)     # Blue for Z-axis
        
        half_size = self.grid_size // 2
        step = self.grid_size // self.grid_divisions
        
        # Draw lines parallel to Z axis (spaced along X)
        for x in range(-half_size, half_size + 1, step):
            pt1 = (x, self.grid_y, -half_size)
            pt2 = (x, self.grid_y, half_size)
            color = axis_color_z if x == 0 else grid_color
            thickness = 2 if x == 0 else 1
            self.draw_line_3d(surface, pt1, pt2, color, thickness)
            
        # Draw lines parallel to X axis (spaced along Z)
        for z in range(-half_size, half_size + 1, step):
            pt1 = (-half_size, self.grid_y, z)
            pt2 = (half_size, self.grid_y, z)
            color = axis_color_x if z == 0 else grid_color
            thickness = 2 if z == 0 else 1
            self.draw_line_3d(surface, pt1, pt2, color, thickness)

    def get_cube_vertices_edges(self, center, size):
        """Calculates 3D vertices and edge connections for a cube at center."""
        cx, cy, cz = center
        s = size / 2
        
        # 8 vertices of the cube
        vertices = [
            (cx - s, cy - s, cz - s),  # 0
            (cx + s, cy - s, cz - s),  # 1
            (cx + s, cy + s, cz - s),  # 2
            (cx - s, cy + s, cz - s),  # 3
            (cx - s, cy - s, cz + s),  # 4
            (cx + s, cy - s, cz + s),  # 5
            (cx + s, cy + s, cz + s),  # 6
            (cx - s, cy + s, cz + s)   # 7
        ]
        
        # 12 edges connecting the vertices
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
            (0, 4), (1, 5), (2, 6), (3, 7)   # Connections
        ]
        
        return vertices, edges

    def draw_cube(self, surface, center, size, color, thickness=2, dotted_faces=False):
        """Draws a 3D wireframe cube at the specified center and size."""
        vertices, edges = self.get_cube_vertices_edges(center, size)
        
        # Project all vertices
        proj_vertices = [self.project_point(v) for v in vertices]
        
        # Draw edges
        for edge in edges:
            v1_idx, v2_idx = edge
            proj1 = proj_vertices[v1_idx]
            proj2 = proj_vertices[v2_idx]
            
            if proj1 and proj2:
                pygame.draw.line(surface, color, proj1, proj2, thickness)
                
        # Optional overlay: transparent fills for faces to give a holographic feel
        if dotted_faces:
            # Renders a subtle cross pattern or point indicator on faces to improve depth perception
            proj_center = self.project_point(center)
            if proj_center:
                pygame.draw.circle(surface, color, proj_center, 3)

    def orbit(self, delta_yaw, delta_pitch):
        """Orbits the camera by modifying yaw and pitch."""
        self.yaw = (self.yaw + delta_yaw) % 360
        self.pitch = max(-85, min(85, self.pitch + delta_pitch))

    def zoom(self, factor):
        """Zooms the camera closer or further."""
        self.camera_z = max(200, min(1500, self.camera_z + factor))
