import tkinter as tk
from tkinter import ttk, messagebox
from gtts import gTTS
import os
import pygame
from googletrans import Translator
import asyncio
import time

# Constants
TEMP_AUDIO_FILE = "temp_speech.mp3"
FONT_PRIMARY = ("Segoe UI", 12)
FONT_SECONDARY = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
COLOR_BG = "#f5f5f5"
COLOR_FRAME = "#ffffff"
COLOR_BUTTON = "#4a6fa5"
COLOR_BUTTON_ACTIVE = "#3a5a80"
COLOR_TEXT = "#333333"

class ModernTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Speech Converter")
        self.root.geometry("520x500")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)
        
        # Initialize pygame mixer with proper settings
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Configure styles
        self.setup_styles()
        
        # Main container
        main_frame = tk.Frame(root, bg=COLOR_FRAME, padx=20, pady=20, 
                            relief=tk.FLAT, bd=0)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(main_frame, text="TEXT TO SPEECH CONVERTER", 
                         font=FONT_TITLE, fg=COLOR_TEXT, bg=COLOR_FRAME)
        header.pack(pady=(0, 15))
        
        # Text input with scrollbar
        text_frame = tk.Frame(main_frame, bg=COLOR_FRAME)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_input = tk.Text(text_frame, height=8, width=50, 
                                font=FONT_PRIMARY, wrap=tk.WORD,
                                padx=10, pady=10, relief=tk.SOLID, bd=1)
        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=self.text_input.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_input.config(yscrollcommand=scrollbar.set)
        
        # Character counter
        self.char_count = tk.Label(main_frame, text="0 characters", 
                                 font=FONT_SECONDARY, fg="#666666", bg=COLOR_FRAME)
        self.char_count.pack(anchor="e", pady=(5, 0))
        self.text_input.bind("<KeyRelease>", self.update_counter)
        
        # Settings frame
        settings_frame = tk.Frame(main_frame, bg=COLOR_FRAME)
        settings_frame.pack(fill=tk.X, pady=(15, 10))
        
        # Language selection
        tk.Label(settings_frame, text="Language:", font=FONT_SECONDARY, 
               fg=COLOR_TEXT, bg=COLOR_FRAME).grid(row=0, column=0, sticky="w")
        
        self.languages = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Japanese': 'ja'
        }
        
        self.lang_var = tk.StringVar(value='English')
        lang_menu = ttk.Combobox(settings_frame, textvariable=self.lang_var,
                                values=list(self.languages.keys()), 
                                state="readonly", font=FONT_PRIMARY)
        lang_menu.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Speed selection
        tk.Label(settings_frame, text="Speed:", font=FONT_SECONDARY, 
               fg=COLOR_TEXT, bg=COLOR_FRAME).grid(row=1, column=0, sticky="w", pady=(10, 0))
        
        self.speed_var = tk.StringVar(value="Normal")
        speed_frame = tk.Frame(settings_frame, bg=COLOR_FRAME)
        speed_frame.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="w")
        
        ttk.Radiobutton(speed_frame, text="Normal", variable=self.speed_var, 
                       value="Normal").pack(side=tk.LEFT)
        ttk.Radiobutton(speed_frame, text="Fast (1.5x)", variable=self.speed_var, 
                       value="Fast").pack(side=tk.LEFT, padx=10)
        
        # Convert button
        convert_btn = tk.Button(main_frame, text="CONVERT TO SPEECH", 
                              command=self.convert_to_speech,
                              font=FONT_SECONDARY, fg="white", bg=COLOR_BUTTON,
                              activebackground=COLOR_BUTTON_ACTIVE,
                              relief=tk.FLAT, padx=20, pady=8)
        convert_btn.pack(pady=(15, 0), fill=tk.X)
        
        # Control buttons
        self.control_frame = tk.Frame(main_frame, bg=COLOR_FRAME)
        
        style = ttk.Style()
        style.configure("Control.TButton", font=FONT_SECONDARY, padding=5)
        
        self.pause_btn = ttk.Button(self.control_frame, text="Pause", 
                                   style="Control.TButton",
                                   command=self.pause_audio)
        self.resume_btn = ttk.Button(self.control_frame, text="Resume", 
                                    style="Control.TButton",
                                    command=self.resume_audio)
        self.stop_btn = ttk.Button(self.control_frame, text="Stop", 
                                 style="Control.TButton",
                                 command=self.stop_audio)
        
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.resume_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.hide_controls()
        
        # Initialize audio state
        self.audio_playing = False
        self.paused = False
        self.monitor_id = None
        self.current_file = None
        
        # Cleanup on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', font=FONT_PRIMARY, padding=5)
        style.configure('TButton', font=FONT_SECONDARY, padding=6)
        style.map('TButton',
                 background=[('active', COLOR_BUTTON_ACTIVE)],
                 foreground=[('active', 'white')])
    
    def update_counter(self, event=None):
        text = self.text_input.get("1.0", tk.END)
        count = len(text) - 1
        self.char_count.config(text=f"{count} characters")
    
    async def async_convert(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Error", "Please enter some text.")
            return
        
        lang = self.languages[self.lang_var.get()]
        
        try:
            # Translate if not English
            if lang != 'en':
                translator = Translator()
                text = translator.translate(text, dest=lang).text
            
            # Create speech with adjusted speed
            slow_speed = False if self.speed_var.get() == "Fast" else True
            tts = gTTS(text=text, lang=lang, slow=slow_speed)
            
            # Clean up any previous audio
            self.cleanup_audio()
            
            # Generate unique filename for each conversion
            timestamp = str(int(time.time()))
            temp_file = f"temp_speech_{timestamp}.mp3"
            self.current_file = temp_file
            
            # Save and play
            tts.save(temp_file)
            
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            self.audio_playing = True
            self.paused = False
            self.show_controls()
            self.monitor_playback()
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
    
    def convert_to_speech(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_convert())
        loop.close()
    
    def monitor_playback(self):
        if self.monitor_id:
            self.root.after_cancel(self.monitor_id)
            
        if self.paused:
            self.monitor_id = self.root.after(100, self.monitor_playback)
        elif pygame.mixer.music.get_busy():
            self.monitor_id = self.root.after(100, self.monitor_playback)
        else:
            self.cleanup_audio()
    
    def pause_audio(self):
        if self.audio_playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            self.pause_btn.pack_forget()
            self.resume_btn.pack(side=tk.LEFT, padx=5)
    
    def resume_audio(self):
        if self.audio_playing and self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.resume_btn.pack_forget()
            self.pause_btn.pack(side=tk.LEFT, padx=5)
    
    def stop_audio(self):
        if self.audio_playing:
            self.cleanup_audio()
    
    def show_controls(self):
        self.control_frame.pack(pady=(15, 0))
        self.resume_btn.pack_forget()
        self.pause_btn.pack(side=tk.LEFT, padx=5)
    
    def hide_controls(self):
        self.control_frame.pack_forget()
    
    def cleanup_audio(self):
        if self.monitor_id:
            self.root.after_cancel(self.monitor_id)
            self.monitor_id = None
            
        pygame.mixer.music.stop()
        
        # Wait briefly to ensure file is released
        time.sleep(0.1)
        
        # Clean up any temporary files
        if self.current_file and os.path.exists(self.current_file):
            try:
                os.remove(self.current_file)
            except Exception as e:
                print(f"Error removing file: {e}")
                # Queue for deletion on next run
                try:
                    os.system(f"del {self.current_file}")
                except:
                    pass
        
        # Clean up any old temp files
        for file in os.listdir():
            if file.startswith("temp_speech_") and file.endswith(".mp3"):
                try:
                    os.remove(file)
                except:
                    pass
        
        self.audio_playing = False
        self.paused = False
        self.hide_controls()
        self.current_file = None
    
    def on_close(self):
        self.cleanup_audio()
        pygame.mixer.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTTSApp(root)
    root.mainloop()