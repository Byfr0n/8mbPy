import os
import sys
import ffmpeg
import cv2
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

def get_video_size(file_path):
    return os.path.getsize(file_path)

def compress_video(input_video, output_video, target_size_mb=8, initial_audio_bitrate=128):
    target_size_bytes = target_size_mb * 1024 * 1024
    min_video_bitrate = 500
    min_audio_bitrate = 64
    initial_size = get_video_size(input_video)

    if initial_size <= target_size_bytes:
        os.rename(input_video, output_video)
        return

    probe = ffmpeg.probe(input_video)
    duration = float(probe['format']['duration'])
    current_audio_bitrate = initial_audio_bitrate
    current_video_bitrate = (target_size_bytes * 8) / (duration * 1000) - current_audio_bitrate

    while current_video_bitrate > min_video_bitrate and current_audio_bitrate > min_audio_bitrate:
        try:
            ffmpeg.input(input_video).output(
                output_video,
                video_bitrate=f'{int(current_video_bitrate)}k',
                audio_bitrate=f'{int(current_audio_bitrate)}k'
            ).run(quiet=True)
            if get_video_size(output_video) <= target_size_bytes:
                break
        except ffmpeg.Error as e:
            print(f"[ERROR] During compression {e}")
            break
        current_video_bitrate *= 0.9
        current_audio_bitrate *= 0.9

def crop_video(input_video, output_video, start_time, end_time):
    try:
        ffmpeg.input(input_video, ss=start_time, to=end_time).output(output_video).run(quiet=True)
    except ffmpeg.Error as e:
        print(f"[ERROR] During cropping {e}")

def prompt_crop(input_video):
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("[ERROR] Unable to open video.")
        return None, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    start_time, end_time = None, None
    is_playing = False

    def update_frame(frame_number=None):
        if frame_number is None:
            frame_number = scale.get()

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(img_pil)

            # huizadhuasdfhsadcvhusdhi8swdgim gonna kill myself
            video_label.img_tk = img_tk  
            video_label.configure(image=img_tk)


    def toggle_play_pause():
        nonlocal is_playing
        is_playing = not is_playing
        play_button.config(text="Pause" if is_playing else "Play")
        if is_playing:
            threading.Thread(target=play_video, daemon=True).start()

    def play_video():
        nonlocal is_playing
        if is_playing:
            current_frame = scale.get()
            if current_frame < frame_count - 1:
                scale.set(current_frame + 1)
                update_frame(current_frame + 1)
                root.after(int(1000 / fps), play_video)
            else:
                play_button.config(text="Play")
                is_playing = False


    def set_start():
        nonlocal start_time
        start_time = scale.get() / fps
        start_label.config(text=f"Start: {start_time:.2f}s")

    def set_end():
        nonlocal end_time
        end_time = scale.get() / fps
        end_label.config(text=f"End: {end_time:.2f}s")

    root = tk.Tk()
    root.title("Crop Video")
    root.configure(bg="#1E1E1E")
    root.geometry("600x400")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", foreground="white", background="#444", padding=5)
    style.configure("TScale", background="#1E1E1E", troughcolor="#333", sliderlength=15, sliderrelief="flat")

    scale = ttk.Scale(root, from_=0, to=frame_count - 1, orient=tk.HORIZONTAL, length=500, command=update_frame)
    scale.pack(pady=10)

    video_label = tk.Label(root, bg="#1E1E1E")
    video_label.pack(pady=10)

    controls = tk.Frame(root, bg="#1E1E1E")
    controls.pack()

    play_button = ttk.Button(controls, text="Play", command=toggle_play_pause)
    play_button.grid(row=0, column=0, padx=5)

    ttk.Button(controls, text="Set Start", command=set_start).grid(row=0, column=1, padx=5)
    ttk.Button(controls, text="Set End", command=set_end).grid(row=0, column=2, padx=5)
    ttk.Button(controls, text="Done", command=root.destroy).grid(row=0, column=3, padx=5)

    start_label = tk.Label(root, text="Start: 0.00s", bg="#1E1E1E", fg="white")
    start_label.pack()
    end_label = tk.Label(root, text="End: 0.00s", bg="#1E1E1E", fg="white")
    end_label.pack()

    update_frame(0)
    root.mainloop()
    cap.release()

    return (start_time, end_time) if start_time and end_time and start_time < end_time else (None, None)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Drag and drop your video")
        sys.exit(1)

    input_video = sys.argv[1]
    output_video = f"compressed_{os.path.basename(input_video)}"

    root = tk.Tk()
    root.withdraw()
    if tk.messagebox.askyesno("Crop Video?", "Do you want to crop the video?"):
        start, end = prompt_crop(input_video)
        if start is not None and end is not None:
            cropped_video = f"cropped_{os.path.basename(input_video)}"
            crop_video(input_video, cropped_video, start, end)
            input_video = cropped_video

    compress_video(input_video, output_video, target_size_mb=8)
