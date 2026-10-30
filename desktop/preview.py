"""Optional local Tk/Pillow preview; frame images are not written to disk."""

import queue
import threading
import tkinter as tk
from tkinter import ttk
from io import BytesIO

from PIL import Image, ImageTk

from desktop.ingest import LatestFrameStore


class PreviewWindow:
    def __init__(self, store: LatestFrameStore) -> None:
        self.store = store
        self.root = tk.Tk()
        self.root.title("Skeleton Mirror - incoming frame (mock or camera)")
        self.label = ttk.Label(self.root, text="Waiting for frames...")
        self.label.pack()
        self.status = ttk.Label(self.root, text="")
        self.status.pack()
        self.photo = None
        self.root.after(50, self.refresh)

    def refresh(self) -> None:
        try:
            frame = self.store.queue.get_nowait()
        except queue.Empty:
            self.root.after(50, self.refresh)
            return
        image = Image.open(BytesIO(frame.jpeg)).convert("RGB")
        self.photo = ImageTk.PhotoImage(image)
        self.label.configure(image=self.photo, text="")
        self.status.configure(
            text=f"{frame.metadata['source']} | frame {frame.metadata['frame_id']} | "
            f"dropped {self.store.dropped_frames} | {pose_text}"
        )
        self.root.after(1, self.refresh)

    @staticmethod
    def draw_pose(image: Image.Image, pose) -> None:
        from PIL import ImageDraw

        draw = ImageDraw.Draw(image)
        w, h = image.size
        for person in pose.persons:
            pts = {l.id: (l.x * w, l.y * h) for l in person.landmarks if l.visibility > 0.3}
            for a, b in POSE_EDGES:
                if a in pts and b in pts:
                    draw.line([pts[a], pts[b]], fill=(0, 255, 0), width=3)
            for x, y in pts.values():
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 0, 0))

    def run(self, server_thread: threading.Thread) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.mainloop()
