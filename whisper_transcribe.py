import whisper
import wave
import os
import time
import sys
import tempfile

# Ensure FFmpeg is available
if not os.system("ffmpeg -version"):
    print("FFmpeg is installed.")
else:
    print("FFmpeg is not installed or not in PATH. Please install FFmpeg.")
    sys.exit(1)

# Load Whisper model
try:
    model = whisper.load_model("base", download_root="C:\\WhisperModels")
except Exception as e:
    print(f"Failed to load Whisper model: {e}")
    print("Ensure the model is downloaded and the path is correct.")
    sys.exit(1)

# Define the path to your pre-recorded WAV file (INPUT)
audio_file = r"C:\Users\felix\Desktop\sops.wav"  # Replace this with your WAV file path

# Check if the WAV file exists
if not os.path.exists(audio_file):
    print(f"Audio file not found: {audio_file}")
    sys.exit(1)

# Convert the WAV file to 16-bit PCM, mono, 16kHz using ffmpeg
try:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name
    ffmpeg_command = f"ffmpeg -y -i {audio_file} -ar 16000 -ac 1 -acodec pcm_s16le {temp_wav_path}"
    if os.system(ffmpeg_command):
        print("Failed to convert WAV file using ffmpeg.")
        sys.exit(1)
    audio_file = temp_wav_path
    print("WAV file successfully converted to 16-bit PCM, mono, 16kHz.")
except Exception as e:
    print(f"Failed to convert WAV file: {e}")
    sys.exit(1)

# Verify WAV file format (should be 16-bit, 16kHz, mono)
try:
    with wave.open(audio_file, 'rb') as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            print("Audio file must be WAV format, mono, 16-bit PCM, 16kHz sample rate.")
            print("Use FFmpeg to convert: ffmpeg -i input.wav -ar 16000 -ac 1 output.wav")
            sys.exit(1)
except Exception as e:
    print(f"Failed to read WAV file: {e}")
    sys.exit(1)

# Transcribe the audio
try:
    result = model.transcribe(audio_file)
    transcript = result["text"]
except Exception as e:
    print(f"Transcription failed: {e}")
    sys.exit(1)

# Define the path to save the transcribed note in Obsidian (OUTPUT)
vault_path = r"C:\Users\felix\Documents\Obisdian\Knowledge\SOPs"  # Replace this with your Obsidian vault path
if not os.path.exists(vault_path):
    print(f"Vault path does not exist: {vault_path}")
    sys.exit(1)

# Create a timestamped filename and save the transcript
timestamp = time.strftime("%Y%m%d-%H%M%S")
filename = os.path.join(vault_path, f"QuickVoiceNote-{timestamp}.md")
with open(filename, 'w', encoding='utf-8') as f:
    f.write(transcript)
print(f"Transcribed to {filename}")