import os
import sys
import subprocess
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

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

    # Transcribe & translate from Chinese to English with timestamps
    segments, _ = model.transcribe(audio_file, task="translate", language="zh", word_timestamps=True)

    # Store transcription result with timestamps
    transcript_data = []
    for segment in segments:
        for word in segment.words:
            transcript_data.append((word.start, word.end, word.word))

    os.remove(audio_file)  # Cleanup temp audio file
    return transcript_data

# Function to add subtitles to the video
def add_subtitles(video_path, transcript_data, output_path="video_with_subtitles.mp4"):
    print("🎬 Adding subtitles to video...")

    # Load video
    video = VideoFileClip(video_path)
    subtitle_clips = []

    # Create subtitle clips
    for start, end, word in transcript_data:
        text = TextClip(word, fontsize=40, color='white', bg_color='black')
        text = text.set_position(("center", "bottom")).set_start(start).set_end(end)
        subtitle_clips.append(text)

    # Overlay subtitles on video
    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_path, codec="libx264", fps=video.fps)

    print(f"✅ Video saved with subtitles: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]
    transcript = transcribe_translate(video_path)

    if transcript:
        add_subtitles(video_path, transcript)
