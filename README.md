# Neon Wireframe AR Builder 🪐

A lightweight, real-time 3D wireframe hologram builder that runs directly inside your webcam feed using computer vision—no heavy 3D engines required. 

This project maps real-time hand gestures and depth estimation to a custom localized 3D workspace, allowing you to manipulate and build neon voxel structures out of thin air. 

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Computer Vision:** OpenCV, MediaPipe (Hands Solution)
* **Graphics & UI:** Pygame
* **Matrix Mathematics:** NumPy

---

## 🚀 How It Works & Controls

The system tracks your hand landmarks via a standard webcam, translates the 2D pixel coordinates and calculated depth into a 3D coordinate system, and flushes the output to a custom rendering pipeline.

### 🎮 Gesture Cheatsheet
* **🤏 Index Pinch (Thumb + Index Tip):** Spawn a neon cube at the snapped grid coordinate.
* **✊ Middle Pinch (Thumb + Middle Tip):** Grab the workspace to rotate/orbit the camera view.
* **⌨️ Keyboard 1, 2, 3, 4:** Cycle through high-contrast neon colors.
* **⌨️ Keyboard U / C:** **U**ndo last block / **C**lear entire workspace.
* **🖱️ Mouse Scroll Wheel:** Manual Depth ($Z$-axis) override if running in webcam-fallback mode.

---

## 📐 The Math Behind the Engine

Instead of abstracting the engine mechanics to Unity or Three.js, the core graphics pipeline is built from scratch using raw linear algebra:

1. **Perspective Projection:** Turning 3D points $(X, Y, Z)$ into flat 2D screen coordinates $(X_{screen}, Y_{screen})$ using a similar-triangles geometric proof scaled by a custom `focal_length`.
2. **Combined View Matrix:** Avoids sequential axis rotations (and the resulting gimbal lock) by computing a single $3 \times 3$ transformation matrix using NumPy dot products (`np.dot`) once per frame.
3. **Spatial Hashing:** Keeps lookup speeds at $O(1)$ by converting floating-point hand locations into distinct structural coordinate keys inside a Python dictionary, preventing duplicate overlapping block spawns.

---

## ✨ Key Features & Hardware Optimization

* **Zero-GPU Requirement:** Optimized matrix operations mean this engine runs smoothly at 60 FPS on basic, everyday integrated-graphics laptops.
* **Hybrid Fallback Mode:** Automatically detects if a webcam is missing or disconnected and seamlessly ports the workspace controls to interactive mouse vectors.
* **Cyberpunk HUD Overlay:** Features a high-contrast industrial diagnostic layout rendered natively over Pygame surface layers.

---

## 💻 Installation & Setup

Get the environment running locally in less than two minutes:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/neon-ar-builder.git](https://github.com/YOUR_USERNAME/neon-ar-builder.git)
   cd neon-ar-builder
