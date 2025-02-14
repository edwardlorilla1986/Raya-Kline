import os
import sys
import subprocess
import textwrap
from moviepy.video.tools.subtitles import SubtitlesClip
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip


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
    segments, _ = model.transcribe(audio_file, task="translate", language="zh", word_timestamps=False)

    # Store transcription result with timestamps
    transcript_data = []
    transcript_text = ""

    for segment in segments:
        start_time = segment.start
        end_time = segment.end
        text = segment.text.strip()

        transcript_data.append((text, start_time, end_time))
        transcript_text += f"[{start_time:.2f}s - {end_time:.2f}s] {text}\n"

    os.remove(audio_file)  # Cleanup temp audio file

    # Save transcript text for reference
    transcript_file = video_file.replace(".mp4", "_translated.txt")
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    print(f"✅ Transcript saved: {transcript_file}")
    return transcript_data, transcript_file

def add_subtitles(video_path, transcript_data, output_path="video_with_subtitles.mp4"):
    print("🎬 Adding subtitles...")

    video = VideoFileClip(video_path)

    # 🎨 CUSTOMIZATION OPTIONS
    font_size = max(24, int(min(video.h, video.w) * 0.05))
    max_chars_per_line = max(20, int(video.w / 30))
    bg_height = int(font_size * 2)
    subtitle_y_position = video.h - bg_height - 30

    text_color = "yellow"
    stroke_color = "black"
    stroke_width = 3
    bg_opacity = 0.6
    font_style = "Arial"  # Change if Arial is not installed

    def render_subtitle(txt, start, end):
        wrapped_text = "\n".join(textwrap.wrap(txt, width=max_chars_per_line))
        print(f"🔤 Subtitle: '{wrapped_text}' from {start:.2f}s to {end:.2f}s")  # Debugging

        bg_clip = ColorClip(size=(video.w, bg_height), color=(0, 0, 0)).set_opacity(bg_opacity).set_duration(max(end - start, 2)).set_start(start).set_position(("center", subtitle_y_position))

        text_clip = TextClip(
            wrapped_text, fontsize=font_size, color=text_color,
            stroke_color=stroke_color, stroke_width=stroke_width, font=font_style
        ).set_duration(max(end - start, 2)).set_start(start).set_position(("center", subtitle_y_position + 5))

        return CompositeVideoClip([bg_clip, text_clip])

    subtitle_clips = [render_subtitle(text, start, end) for text, start, end in transcript_data]

    if not subtitle_clips:
        print("⚠️ No subtitles generated! Check transcription.")

    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_path, codec="libx264", fps=video.fps, preset="medium", threads=4)

    print(f"✅ Video saved: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <video_file>")
        sys.exit(1)

    video_path = sys.argv[1]
    transcript, transcript_file = transcribe_translate(video_path)

    if transcript:
        add_subtitles(video_path, transcript)
        print(f"📄 Transcript Reference File: {transcript_file}")
