import os
import subprocess
from faster_whisper import Whisper

# Function to extract audio from video
def extract_audio(video_path, audio_path="temp_audio.wav"):
    command = f"ffmpeg -i {video_path} -ar 16000 -ac 1 -c:a pcm_s16le {audio_path} -y"
    subprocess.run(command, shell=True, check=True)
    return audio_path

# Function to transcribe and translate
def transcribe_translate(video_file, model_size="large-v2"):
    # Extract audio from video
    audio_file = extract_audio(video_file)

    # Load Faster Whisper model
    model = Whisper(model_size)

    # Transcribe and translate from Chinese to English
    segments, _ = model.transcribe(audio_file, task="translate", language="zh")

    # Store transcription result
    transcript = "\n".join(segment.text for segment in segments)

    # Save the transcript
    transcript_file = video_file.replace(".mp4", "_translated.txt")
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript)

    print(f"\n✅ Transcription saved: {transcript_file}")
    os.remove(audio_file)  # Cleanup temp audio file
    return transcript_file

# Run the script
if __name__ == "__main__":
    transcribe_translate("videos/1.mp4")
