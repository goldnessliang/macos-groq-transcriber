import tkinter
import tkinter.filedialog
import customtkinter
import os
import threading
import json # For saving/loading the key
from pathlib import Path # For easier path handling
from groq import Groq, GroqError

# --- Configuration ---
APP_NAME = "TranscriberApp"
CONFIG_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

# Appearance Settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Language Data (Keep as before)
SUPPORTED_LANGUAGES = [
    "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
    "ar", "hi", "nl", "pl", "sv", "tr", "uk", "vi", "el", "he"
]
LANGUAGE_MAP = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
    "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
    "nl": "Dutch", "pl": "Polish", "sv": "Swedish", "tr": "Turkish",
    "uk": "Ukrainian", "vi": "Vietnamese", "el": "Greek", "he": "Hebrew"
}
DISPLAY_LANGUAGES = sorted([f"{name} ({code})" for code, name in LANGUAGE_MAP.items() if code in SUPPORTED_LANGUAGES])
CODE_FROM_DISPLAY = {f"{name} ({code})": code for code, name in LANGUAGE_MAP.items() if code in SUPPORTED_LANGUAGES}

# --- Helper Functions for API Key ---
def ensure_config_dir_exists():
    """Creates the configuration directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_api_key(api_key):
    """Saves the API key to the config file."""
    ensure_config_dir_exists()
    config_data = {"groq_api_key": api_key}
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
        return True
    except IOError as e:
        print(f"Error saving API key: {e}")
        return False

def load_api_key():
    """Loads the API key from the config file."""
    if not CONFIG_FILE.is_file():
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
            return config_data.get("groq_api_key")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading API key: {e}")
        return None

# --- Main Application Class ---
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Audio Transcriber (Groq Whisper)")
        self.geometry("700x700") # Increased height for API key section
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Make text box row expandable

        # --- State Variables ---
        self.selected_filepath = ""
        self.groq_client = None
        self.api_key = load_api_key() # Load key at startup
        self.selected_language_code = "en"

        # --- UI Elements ---

        # --- API Key Frame ---
        self.api_key_frame = customtkinter.CTkFrame(self)
        self.api_key_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.api_key_frame.grid_columnconfigure(1, weight=1) # Make entry expand

        self.api_key_label = customtkinter.CTkLabel(self.api_key_frame, text="Groq API Key:")
        self.api_key_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

        self.api_key_entry = customtkinter.CTkEntry(self.api_key_frame, show="*", width=350)
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        if self.api_key:
            self.api_key_entry.insert(0, self.api_key) # Pre-fill if loaded

        self.save_key_button = customtkinter.CTkButton(self.api_key_frame, text="Save Key", width=100, command=self.save_key_and_reinit)
        self.save_key_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        self.api_key_status_label = customtkinter.CTkLabel(self.api_key_frame, text="", text_color="grey")
        self.api_key_status_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")
        # --- End API Key Frame ---

        # File Selection Frame
        self.file_frame = customtkinter.CTkFrame(self)
        self.file_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew") # Adjusted pady
        self.file_frame.grid_columnconfigure(1, weight=1)

        self.select_button = customtkinter.CTkButton(self.file_frame, text="Select Audio File", command=self.select_file)
        self.select_button.grid(row=0, column=0, padx=10, pady=10)

        self.file_label = customtkinter.CTkLabel(self.file_frame, text="No file selected", anchor="w")
        self.file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Options Frame (Language + Transcribe Button)
        self.options_frame = customtkinter.CTkFrame(self)
        self.options_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.options_frame.grid_columnconfigure(2, weight=1)

        self.language_label = customtkinter.CTkLabel(self.options_frame, text="Audio Language:")
        self.language_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

        self.language_combo = customtkinter.CTkComboBox(
            self.options_frame, values=DISPLAY_LANGUAGES, command=self.language_selected, width=180
        )
        default_lang_display = f"{LANGUAGE_MAP[self.selected_language_code]} ({self.selected_language_code})"
        self.language_combo.set(default_lang_display)
        self.language_selected(default_lang_display) # Set initial code
        self.language_combo.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.transcribe_button = customtkinter.CTkButton(self.options_frame, text="Transcribe", command=self.start_transcription_thread, state="disabled")
        self.transcribe_button.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="e")

        # Result Text Box
        self.result_textbox = customtkinter.CTkTextbox(self, wrap="word", state="disabled")
        self.result_textbox.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="nsew")

        # Copy Button
        self.copy_button = customtkinter.CTkButton(self, text="Copy Text", command=self.copy_to_clipboard, state="disabled")
        self.copy_button.grid(row=4, column=0, padx=20, pady=(0, 5), sticky="e")

        # Status Label
        self.status_label = customtkinter.CTkLabel(self, text="Status: Ready", anchor="w")
        self.status_label.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # --- Initial Groq Client Initialization ---
        self.initialize_groq_client() # Try to init with loaded key

    # --- Methods ---

    def initialize_groq_client(self):
        """Tries to initialize the Groq client with the current self.api_key."""
        if not self.api_key:
            self.api_key_status_label.configure(text="API Key required.", text_color="orange")
            self.groq_client = None
            self.update_transcribe_button_state() # Ensure button is disabled
            return False

        try:
            self.groq_client = Groq(api_key=self.api_key)
            # Optional: Add a lightweight check if Groq API provides one, e.g., list models
            # For now, assume initialization success means the key format is likely okay.
            self.api_key_status_label.configure(text="API Key loaded and seems valid.", text_color="green")
            self.update_transcribe_button_state() # Update button state based on file selection
            return True
        except (GroqError, Exception) as e:
            print(f"Groq client initialization failed: {e}")
            self.groq_client = None
            self.api_key_status_label.configure(text=f"Failed to initialize Groq client. Check key. Error: {type(e).__name__}", text_color="red")
            self.update_transcribe_button_state() # Ensure button is disabled
            return False

    def save_key_and_reinit(self):
        """Saves the key from the entry field and re-initializes the client."""
        entered_key = self.api_key_entry.get()
        if not entered_key:
            self.api_key_status_label.configure(text="Cannot save an empty API Key.", text_color="orange")
            return

        if save_api_key(entered_key):
            self.api_key = entered_key # Update the key in memory
            self.api_key_status_label.configure(text="API Key saved. Validating...", text_color="grey")
            # Re-initialize the client with the new key
            self.initialize_groq_client()
        else:
            self.api_key_status_label.configure(text="Error saving API Key to file.", text_color="red")

    def update_transcribe_button_state(self):
        """Enables or disables the transcribe button based on file selection and client status."""
        if self.selected_filepath and self.groq_client:
            self.transcribe_button.configure(state="normal")
        else:
            self.transcribe_button.configure(state="disabled")

    def select_file(self):
        """Opens a file dialog to select an audio file."""
        filepath = tkinter.filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=(("Audio Files", "*.wav *.mp3 *.m4a *.ogg *.flac"), ("All Files", "*.*"))
        )
        if filepath:
            self.selected_filepath = filepath
            filename = os.path.basename(filepath)
            self.file_label.configure(text=filename)
            self.status_label.configure(text="Status: File selected.")
            self.result_textbox.configure(state="normal")
            self.result_textbox.delete("1.0", "end")
            self.result_textbox.configure(state="disabled")
            self.copy_button.configure(state="disabled")
            self.update_transcribe_button_state() # Check if button can be enabled
        else:
            pass # No change if cancelled

    def language_selected(self, selected_display_language):
        """Updates the selected language code when the combobox changes."""
        self.selected_language_code = CODE_FROM_DISPLAY.get(selected_display_language, "en")

    def start_transcription_thread(self):
        """Starts the transcription process in a separate thread."""
        if not self.selected_filepath or not self.groq_client:
            self.status_label.configure(text="Status: Error - Select file and ensure API key is valid.")
            return

        # Disable buttons
        self.transcribe_button.configure(state="disabled", text="Transcribing...")
        self.select_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.language_combo.configure(state="disabled")
        self.save_key_button.configure(state="disabled") # Disable save during transcription
        self.api_key_entry.configure(state="disabled")

        self.status_label.configure(text=f"Status: Processing ({self.selected_language_code})...")
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"Starting transcription (Language: {self.selected_language_code})...\n")
        self.result_textbox.configure(state="disabled")

        thread = threading.Thread(target=self.transcribe_audio)
        thread.start()

    def transcribe_audio(self):
        """Handles the actual API call to Groq."""
        try:
            with open(self.selected_filepath, "rb") as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(os.path.basename(self.selected_filepath), file.read()),
                    model="whisper-large-v3",
                    language=self.selected_language_code,
                    response_format="json",
                )
                result_text = transcription.text
                self.update_ui_after_transcription(result_text, success=True)

        except GroqError as e:
            error_message = f"Groq API Error: {e.status_code} - {e.message}"
            if hasattr(e, 'body') and e.body and 'error' in e.body and 'message' in e.body['error']:
                 error_message += f"\nDetails: {e.body['error']['message']}"
            # Check for specific authentication error
            if e.status_code == 401:
                error_message += "\n(Check if your API Key is correct and active)"
            self.update_ui_after_transcription(error_message, success=False)
        except FileNotFoundError:
            error_message = "Error: Audio file not found."
            self.update_ui_after_transcription(error_message, success=False)
        except Exception as e:
            error_message = f"An unexpected error occurred: {type(e).__name__} - {e}"
            self.update_ui_after_transcription(error_message, success=False)

    def update_ui_after_transcription(self, message, success):
        """Updates the GUI elements after transcription finishes."""
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", message)
        self.result_textbox.configure(state="disabled")

        if success:
            self.status_label.configure(text="Status: Transcription Complete!")
            self.copy_button.configure(state="normal")
        else:
            self.status_label.configure(text="Status: Error during transcription.")
            self.copy_button.configure(state="disabled")

        # Re-enable buttons/entries
        self.select_button.configure(state="normal")
        self.language_combo.configure(state="normal")
        self.save_key_button.configure(state="normal")
        self.api_key_entry.configure(state="normal")
        self.update_transcribe_button_state() # Re-check transcribe button state
        self.transcribe_button.configure(text="Transcribe") # Reset button text


    def copy_to_clipboard(self):
        """Copies the content of the result textbox to the clipboard."""
        try:
            self.result_textbox.configure(state="normal")
            text_to_copy = self.result_textbox.get("1.0", "end-1c")
            self.result_textbox.configure(state="disabled")

            if text_to_copy:
                self.clipboard_clear()
                self.clipboard_append(text_to_copy)
                self.status_label.configure(text="Status: Text copied to clipboard!")
                self.copy_button.configure(text="Copied!")
                self.after(2000, lambda: self.copy_button.configure(text="Copy Text"))
            else:
                self.status_label.configure(text="Status: Nothing to copy.")
        except Exception as e:
            self.status_label.configure(text=f"Status: Error copying text - {e}")
            self.result_textbox.configure(state="disabled")


# --- Run the Application ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
