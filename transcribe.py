import os
import sys
import subprocess
import textwrap
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from gtts import gTTS

# Function to extract audio from video
def extract_audio(video_path, audio_path="temp_audio.wav"):
    """Extracts audio from the video using ffmpeg."""
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file '{video_path}' not found.")
        sys.exit(1)

    command = f"ffmpeg -i {video_path} -ar 16000 -ac 1 -c:a pcm_s16le {audio_path} -y -loglevel error"
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to extract audio. Ensure ffmpeg is installed.")
        sys.exit(1)

    return audio_path

# Function to transcribe and translate video audio
def transcribe_translate(video_file, model_size="large-v2"):
    """Transcribes and translates audio from Chinese to English with timestamps."""
    if not os.path.exists(video_file):
        print(f"❌ Error: File '{video_file}' not found.")
        return None

    print(f"🎙 Processing video: {video_file}")

    # Extract audio
    audio_file = extract_audio(video_file)

    # Load Faster Whisper model
    try:
        model = WhisperModel(model_size)
    except Exception as e:
        print(f"❌ Error loading Whisper model: {e}")
        sys.exit(1)

    # Transcribe & translate
    segments, _ = model.transcribe(audio_file, task="translate", language="zh", word_timestamps=True)

    transcript_data = []
    current_phrase = []
    phrase_start = None

    for segment in segments:
        for word in segment.words:
            if phrase_start is None:
                phrase_start = word.start
            current_phrase.append(word.word)

            # Group words into phrases of ~6 words for better readability
            if len(current_phrase) >= 6 or word == segment.words[-1]:  
                transcript_data.append((" ".join(current_phrase), phrase_start, word.end))
                current_phrase = []
                phrase_start = None

    os.remove(audio_file)  # Cleanup temp audio file
    return transcript_data

# Function to generate speech from captions
def generate_tts_audio(transcript_data, output_audio_path="narration.mp3", lang="en"):
    """Generates speech audio from the translated captions."""
    print("🔊 Generating narration from subtitles...")

    # Combine all text segments for TTS
    full_text = " ".join([text for text, _, _ in transcript_data])

    # Convert text to speech
    tts = gTTS(full_text, lang=lang)
    tts.save(output_audio_path)

    return output_audio_path

# Function to add subtitles to the video
def add_subtitles(video_path, transcript_data, output_path="video_with_subtitles.mp4"):
    """Overlays subtitles onto the video."""
    print("🎬 Adding responsive subtitles to video...")

    # Load video
    video = VideoFileClip(video_path)

    # Auto-scale font size based on both width and height
    font_size = max(20, int(min(video.h, video.w) * 0.05))  # Scale based on the smaller dimension

    # Set max characters per line based on video width
    max_chars_per_line = max(20, int(video.w / 30))  # Dynamically adjust wrapping width

    # Function to render wrapped text with auto-scaling
    def render_subtitle(txt):
        wrapped_text = "\n".join(textwrap.wrap(txt, width=max_chars_per_line))
        text_clip = TextClip(
            wrapped_text, 
            fontsize=font_size, 
            color='white', 
            stroke_color='white', 
            stroke_width=3, 
            transparent=True
        )
        return ColorClip(size=text_clip.size, color=(0, 0, 0), ismask=False).set_opacity(0.5)

    # Create subtitle clips
    subtitle_clips = []
    for text, start, end in transcript_data:
        subtitle = render_subtitle(text).set_position(("center", "top")).set_duration(end - start).set_start(start)
        subtitle_clips.append(subtitle)

    if not subtitle_clips:
        print("⚠️ No subtitle clips were generated! Check transcription output.")

    # Overlay subtitles on video
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Save the final video
    final_video.write_videofile(output_path, codec="libx264", fps=video.fps, preset="medium", threads=4)

    print(f"✅ Video saved with subtitles: {output_path}")

# Function to replace original audio with generated narration
def replace_audio(video_path, narration_audio, output_path="video_with_narration.mp4"):
    """Replaces original audio with generated narration."""
    print("🎬 Replacing original audio with narration...")

    # Load video and narration
    video = VideoFileClip(video_path)
    narration = AudioFileClip(narration_audio)

    # Ensure narration matches video duration
    final_video = video.set_audio(narration)
    final_video.write_videofile(output_path, codec="libx264", fps=video.fps, audio_codec="aac")

    print(f"✅ Video saved with narration replacing original audio: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]
    transcript = transcribe_translate(video_path)

    if transcript:
        # Generate TTS narration
        narration_audio = generate_tts_audio(transcript)

        # Replace original audio with narration
        replace_audio(video_path, narration_audio)

        # Add subtitles to video
        add_subtitles(video_path, transcript)
