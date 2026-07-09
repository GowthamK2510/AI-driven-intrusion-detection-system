import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, simpledialog
from PIL import Image, ImageTk
import threading
import queue
import cv2
import time
import numpy as np
import datetime
import torch
import torch.nn.functional as F
import pyttsx3
import mediapipe as mp
import pickle
import os
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO

# -------------------------------
# Voice Assistant Thread (Jarvis TTS)
# -------------------------------
class VoiceThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.speech_queue = queue.Queue()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170) 
        self.engine.setProperty('volume', 0.9)

    def run(self):
        while True:
            text = self.speech_queue.get()
            if text is None: break 
            self.engine.say(text)
            self.engine.runAndWait()
            self.speech_queue.task_done()

    def speak(self, text):
        self.speech_queue.put(text)

# -------------------------------
# Pose Estimation (MediaPipe)
# -------------------------------
class PoseEstimator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

    def process_and_draw(self, frame, rgb_frame):
        results = self.pose.process(rgb_frame)
        if results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2),
                self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )
        return frame

# -------------------------------
# Detector Class (YOLOv8 on GPU)
# -------------------------------
class Detector:
    def __init__(self, model_path="yolov8n.pt"):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(model_path)
        self.model.to(self.device)
        print(f"[SYSTEM] YOLO loaded on: {self.device.upper()}")

    def detect_and_track(self, frame):
        return self.model.track(frame, persist=True, verbose=False)

# -------------------------------
# THE BRAIN: Local Insight & Memory
# -------------------------------
class LocalInsightModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[SYSTEM] Neural Cortex loading on: {self.device.upper()}...")
        
        self.model = CLIPModel.from_pretrained("./clip-model").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("./clip-model")
        
        self.categories = [
            "a smartphone", "a coffee mug", "a pair of glasses", "a computer keyboard",
            "a pen or pencil", "a smartwatch", "a water bottle", "a set of keys"
        ]
        
        # Initialize the Hippocampus (Long-Term Memory)
        self.memory_file = "jarvis_brain.pkl"
        self.memory_bank = {}
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'rb') as f:
                self.memory_bank = pickle.load(f)
            print(f"[BRAIN] Loaded {len(self.memory_bank)} learned concepts into memory.")
        else:
            print("[BRAIN] Blank memory initialized.")

    def save_memory(self):
        with open(self.memory_file, 'wb') as f:
            pickle.dump(self.memory_bank, f)
        print("[BRAIN] Memory successfully written to disk.")

    def get_fingerprint(self, image_path):
        """Extracts the 512-dimensional math vector representing the image."""
        image = Image.open(image_path)
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
        # Normalize the vector for accurate comparison
        return image_features / image_features.norm(p=2, dim=-1, keepdim=True)

    def learn_object(self, image_path, custom_name):
        """Saves a new object fingerprint to the brain."""
        fingerprint = self.get_fingerprint(image_path)
        if custom_name not in self.memory_bank:
            self.memory_bank[custom_name] = []
        # Store the vector on CPU to save VRAM long-term
        self.memory_bank[custom_name].append(fingerprint.cpu())
        self.save_memory()
        return f"Successfully learned: {custom_name}"

    def identify(self, image_path):
        try:
            # 1. Get the fingerprint of the unknown object
            target_fingerprint = self.get_fingerprint(image_path)
            
            # 2. Check personal memory first (Cosine Similarity)
            best_memory_match = None
            highest_similarity = 0.0
            
            for name, fingerprints in self.memory_bank.items():
                for stored_fp in fingerprints:
                    stored_fp = stored_fp.to(self.device) # Move back to GPU for math
                    similarity = F.cosine_similarity(target_fingerprint, stored_fp).item()
                    
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_memory_match = name

            # 3. If similarity is very high (>85%), it remembers!
            if highest_similarity > 0.85:
                return f"[RECALLED] {best_memory_match}"

            # 4. If not in memory, guess using general knowledge
            image = Image.open(image_path)
            inputs = self.processor(text=self.categories, images=image, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            probs = outputs.logits_per_image.softmax(dim=1)
            best_match = self.categories[probs.argmax().item()]
            return best_match.replace("a ", "").title()
            
        except Exception as e:
            print(f"Brain Error: {e}")
            return "Analysis Error"

# -------------------------------
# Core Tracking & Math
# -------------------------------
class Tracker:
    def __init__(self):
        self.track_history = {}

    def calculate_speed(self, track_id, cx, cy, current_time):
        speed = 0
        if track_id in self.track_history:
            prev_cx, prev_cy, prev_time = self.track_history[track_id]
            dist = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
            time_diff = current_time - prev_time
            if time_diff > 0: speed = dist / time_diff
        self.track_history[track_id] = (cx, cy, current_time)
        return speed

class Visualizer:
    def draw(self, frame, box, track_id, object_name, speed):
        x1, y1, x2, y2 = map(int, box)
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.line(frame, (x1, y1), (x1 + 20, y1), (0, 255, 0), 3)
        cv2.line(frame, (x1, y1), (x1, y1 + 20), (0, 255, 0), 3)
        cv2.line(frame, (x2, y2), (x2 - 20, y2), (0, 255, 0), 3)
        cv2.line(frame, (x2, y2), (x2, y2 - 20), (0, 255, 0), 3)

        color = (0, 165, 255) if "[RECALLED]" in object_name else (0, 255, 255)
        label = f"{object_name} [ID:{track_id}] | V:{int(speed)}px/s"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
        return frame

# -------------------------------
# Tactical GUI (Project Jarvis)
# -------------------------------
class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS Vision Subsystem v2.0 - Active Memory")
        self.root.configure(bg="#121212")

        self.bg_color = "#121212"
        self.fg_color = "#00ff00"
        self.btn_color = "#1e1e1e"
        
        self.conf_threshold = 0.45
        self.enable_pose = tk.BooleanVar(value=False)
        self.enable_voice = tk.BooleanVar(value=True)
        self.known_objects = set() 
        self.teach_flag = False

        self.voice = VoiceThread()
        self.voice.start()
        self.voice.speak("Neural cortex and memory banks online.")
        
        self.local_insight = LocalInsightModel()
        self.pose_estimator = PoseEstimator()
        self.tracker = Tracker()
        self.visualizer = Visualizer()
        
        self.build_ui()
        self.running = False

    def build_ui(self):
        control_frame = tk.Frame(self.root, bg=self.bg_color, width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(control_frame, text="SYS.CONTROLS", bg=self.bg_color, fg=self.fg_color, font=("Consolas", 14, "bold")).pack(pady=10)

        self.model_var = tk.StringVar(value="yolov8n.pt")
        tk.OptionMenu(control_frame, self.model_var, "yolov8n.pt", "yolov8s.pt").pack(pady=5, fill=tk.X)

        self.make_btn(control_frame, "INIT CAMERA", self.use_webcam).pack(pady=5, fill=tk.X)
        self.make_btn(control_frame, "LOAD VIDEO", self.open_video).pack(pady=5, fill=tk.X)
        
        # New Memory Button
        self.make_btn(control_frame, "TEACH ANOMALY", self.trigger_teach_mode, fg="#ff00ff").pack(pady=15, fill=tk.X)
        
        self.make_btn(control_frame, "HALT STREAM", self.stop_pipeline, fg="red").pack(pady=5, fill=tk.X)

        tk.Checkbutton(control_frame, text="Skeletal Tracking", variable=self.enable_pose, bg=self.bg_color, fg="white", selectcolor=self.btn_color, activebackground=self.bg_color, activeforeground="white").pack(pady=5, anchor=tk.W)
        tk.Checkbutton(control_frame, text="Audio Feedback", variable=self.enable_voice, bg=self.bg_color, fg="white", selectcolor=self.btn_color, activebackground=self.bg_color, activeforeground="white").pack(pady=5, anchor=tk.W)

        stream_frame = tk.Frame(self.root, bg=self.bg_color)
        stream_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas = tk.Label(stream_frame, bg="black")
        self.canvas.pack(pady=10)

        self.history_list = tk.Listbox(stream_frame, height=8, bg="#1e1e1e", fg=self.fg_color, font=("Consolas", 10), borderwidth=0)
        self.history_list.pack(fill=tk.X, padx=10)

        self.status_var = tk.StringVar(value="SYSTEM STANDBY")
        tk.Label(self.root, textvariable=self.status_var, bg="#002200", fg="#00ff00", font=("Consolas", 10), anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def make_btn(self, parent, text, command, fg="#00ffff"):
        return tk.Button(parent, text=text, command=command, bg=self.btn_color, fg=fg, font=("Consolas", 10, "bold"), relief=tk.FLAT, borderwidth=1, highlightbackground=fg)

    def trigger_teach_mode(self):
        self.teach_flag = True

    def run_pipeline(self, source):
        self.detector = Detector(model_path=self.model_var.get())
        threading.Thread(target=self.process_source, args=(source,), daemon=True).start()

    def process_source(self, source):
        self.running = True
        cap = cv2.VideoCapture(int(source)) if str(source).isdigit() else cv2.VideoCapture(source)

        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success: break

            current_time = time.time()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if self.enable_pose.get():
                frame = self.pose_estimator.process_and_draw(frame, rgb_frame)

            results = self.detector.detect_and_track(frame)
            
            largest_box = None
            max_area = 0

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu()
                track_ids = results[0].boxes.id.int().cpu().tolist()
                class_indices = results[0].boxes.cls.int().cpu().tolist()
                confidences = results[0].boxes.conf.cpu().tolist()
                names = results[0].names

                for box, track_id, cls_idx, conf in zip(boxes, track_ids, class_indices, confidences):
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

                    # Track largest object for teaching mode
                    area = (x2 - x1) * (y2 - y1)
                    if area > max_area:
                        max_area = area
                        largest_box = (x1, y1, x2, y2)

                    # CLIP Memory Check
                    if conf < self.conf_threshold:
                        h, w, _ = frame.shape
                        crop_x1, crop_y1 = max(0, x1), max(0, y1)
                        crop_x2, crop_y2 = min(w, x2), min(h, y2)
                        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                        
                        if cropped.size > 0:
                            cv2.imwrite("temp_insight.jpg", cropped)
                            object_name = f"*{self.local_insight.identify('temp_insight.jpg')}"
                            
                            if self.enable_voice.get() and object_name not in self.known_objects:
                                clean_name = object_name.replace('*', '').replace('[RECALLED] ', '')
                                self.voice.speak(f"Identified {clean_name}")
                                self.known_objects.add(object_name)
                        else:
                            object_name = "Anomaly"
                    else:
                        object_name = names[cls_idx]

                    speed = self.tracker.calculate_speed(track_id, cx, cy, current_time)
                    frame = self.visualizer.draw(frame, box, track_id, object_name, speed)

            # Teach Mode Execution
            if self.teach_flag:
                self.teach_flag = False # Reset flag immediately
                if largest_box is not None:
                    x1, y1, x2, y2 = largest_box
                    h, w, _ = frame.shape
                    c_x1, c_y1 = max(0, x1), max(0, y1)
                    c_x2, c_y2 = min(w, x2), min(h, y2)
                    cropped_target = frame[c_y1:c_y2, c_x1:c_x2]
                    
                    if cropped_target.size > 0:
                        cv2.imwrite("teach_temp.jpg", cropped_target)
                        # Pause stream briefly to ask user
                        custom_name = simpledialog.askstring("Brain Interface", "What is this object named?", parent=self.root)
                        if custom_name:
                            msg = self.local_insight.learn_object("teach_temp.jpg", custom_name)
                            self.voice.speak(f"Memory updated. I will now recognize {custom_name}.")
                            self.root.after(0, self.update_history, f"[SYSTEM] {msg}")

            self.root.after(0, self.status_var.set, f"MATRIX ACTIVE | FPS: {int(cap.get(cv2.CAP_PROP_FPS))}")

            cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_im = Image.fromarray(cv2_im)
            pil_im.thumbnail((800, 600))
            imgtk = ImageTk.PhotoImage(image=pil_im)
            self.root.after(0, self.update_canvas, imgtk)

        cap.release()
        self.root.after(0, self.status_var.set, "SYSTEM STANDBY")

    def update_history(self, entry):
        self.history_list.insert(0, entry)
        if self.history_list.size() > 15: self.history_list.delete(15)

    def update_canvas(self, imgtk):
        self.canvas.imgtk = imgtk 
        self.canvas.configure(image=imgtk)

    def open_video(self):
        filepath = filedialog.askopenfilename()
        if filepath: self.run_pipeline(filepath)

    def use_webcam(self):
        self.run_pipeline("0")

    def stop_pipeline(self):
        self.running = False
        self.status_var.set("HALTING STREAM...")
        self.known_objects.clear()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x800") 
    app = VisionApp(root)
    def on_closing():
        app.running = False
        app.voice.speech_queue.put(None)
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()