import os
import sys
import subprocess
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import textwrap

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
    current_phrase = []
    phrase_start = None

    for segment in segments:
        for word in segment.words:
            if phrase_start is None:
                phrase_start = word.start
            current_phrase.append(word.word)

            # Group words into phrases of ~6 words for better subtitle readability
            if len(current_phrase) >= 6 or word == segment.words[-1]:  
                transcript_data.append((" ".join(current_phrase), phrase_start, word.end))
                current_phrase = []
                phrase_start = None

    os.remove(audio_file)  # Cleanup temp audio file
    return transcript_data

# Function to add subtitles with overlay background
def add_subtitles(video_path, transcript_data, output_path="video_with_subtitles.mp4"):
    print("🎬 Adding subtitles with overlay background...")

    # Load video
    video = VideoFileClip(video_path)

    # Auto-scale font size based on video dimensions
    font_size = max(20, int(video.h * 0.05))  # Scale font size based on video height

    # Set max characters per line based on video width
    max_chars_per_line = max(20, int(video.w / 30))  # Dynamically adjust wrapping width

    # Adjust line spacing
    line_spacing = int(font_size * 1.5)  

    # Function to render text with overlay background
    def render_subtitle(txt):
        wrapped_text = "\n".join(textwrap.wrap(txt, width=max_chars_per_line))

        # Create text clip (White text with black stroke)
        text_clip = TextClip(
            wrapped_text, fontsize=font_size, color='white', stroke_color='white', stroke_width=3
        )

        # Create a semi-transparent black background using ColorClip
        bg_height = text_clip.h + 20  # Padding for better visibility
        background = ColorClip(size=(video.w, bg_height), color=(0, 0, 0))  # Black overlay
        background = background.set_opacity(0.6)  # Adjust transparency

        # Overlay text on the background
        subtitle = CompositeVideoClip([background, text_clip.set_position("center")])
        return subtitle

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]
    transcript = transcribe_translate(video_path)

    if transcript:
        add_subtitles(video_path, transcript)
