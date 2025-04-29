# macOS Audio Transcriber using Groq Whisper API

A simple desktop application for macOS to transcribe audio files using the Groq API (Whisper model).

## Features

*   Select local audio files (MP3, WAV, M4A, etc.).
*   Choose the audio language for transcription.
*   Displays the transcription result.
*   Copies the transcription text to the clipboard.
*   Saves the Groq API key securely within the app's configuration.

## Requirements

*   macOS
*   Python 3.9+ (Recommended: Install from python.org)
*   Groq API Key (Get one from [https://console.groq.com/](https://console.groq.com/))

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd macos-groq-transcriber # Or your repo name
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Run the application for the first time:
    ```bash
    python transcriber_app.py
    ```
2.  The app window will open. Paste your Groq API Key into the "Groq API Key" field.
3.  Click "Save Key". The key will be stored locally in `~/Library/Application Support/TranscriberApp/config.json`.

## Usage

1.  Ensure the virtual environment is active (`source venv/bin/activate`).
2.  Run the script:
    ```bash
    python transcriber_app.py
    ```
3.  Use the application interface to select a file, choose a language, and transcribe.

## Building the .app (Optional)

1.  Make sure `pyinstaller` is installed (`pip install pyinstaller`).
2.  Run the build command from the project directory:
    ```bash
    pyinstaller --windowed --onefile --name="TranscriberApp" transcriber_app.py
    ```
3.  The `TranscriberApp.app` bundle will be located in the `dist/` folder. You can move this to your `/Applications` folder. The `.app` will read the API key from the configuration file created during the setup step.

## License

[MIT License]
