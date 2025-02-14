import os
import sys
import subprocess
from faster_whisper import WhisperModel

# Function to extract audio from video
def extract_audio(video_path, audio_path="temp_audio.wav"):
    command = f"ffmpeg -i {video_path} -ar 16000 -ac 1 -c:a pcm_s16le {audio_path} -y"
    subprocess.run(command, shell=True, check=True)
    return audio_path

# Function to transcribe and translate with timestamps
def transcribe_translate(video_file, model_size="large-v2"):
    if not os.path.exists(video_file):
        print(f"Error: File {video_file} not found.")
        return

    print(f"🎙 Processing video: {video_file}")

    # Extract audio
    audio_file = extract_audio(video_file)

    # Load Faster Whisper model
    model = WhisperModel(model_size)

    # Transcribe & translate from Chinese to English with word-level timestamps
    segments, _ = model.transcribe(audio_file, task="translate", language="zh", word_timestamps=True)

    # Store transcription result with timestamps
    transcript_file = f"transcripts/{os.path.basename(video_file).replace('.mp4', '_translated.txt')}"

    with open(transcript_file, "w", encoding="utf-8") as f:
        for segment in segments:
            for word in segment.words:
                f.write(f"[{word.start:.2f}s - {word.end:.2f}s] {word.word}\n")

    print(f"✅ Transcription saved with timestamps: {transcript_file}")
    os.remove(audio_file)  # Cleanup temp audio file
    return transcript_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]
    transcribe_translate(video_path)
