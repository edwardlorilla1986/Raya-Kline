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

# Function to add subtitles to the video
def add_subtitles(video_path, transcript_data, output_path="video_with_subtitles.mp4"):
    print("🎬 Adding subtitles to video...")

    # Load video
    video = VideoFileClip(video_path)
    subtitle_clips = []

    # Auto-scale font size based on video height
    font_size = max(30, int(video.h * 0.06))  # Ensure font is large enough

    # Check font availability
    try:
        sample_text = TextClip("Test", fontsize=font_size, color='white', stroke_color='black', stroke_width=2, font="Arial")
        sample_text.close()
    except Exception as e:
        print("⚠️ Font issue detected! Using default font. Error:", str(e))

    # Create subtitle clips
    for text, start, end in transcript_data:
        subtitle = TextClip(
            text, fontsize=font_size, color='white',
            stroke_color='black', stroke_width=2, font="DejaVu-Sans"
        ).set_position(("center", "bottom")).set_duration(end - start).set_start(start)

        subtitle_clips.append(subtitle)

    if not subtitle_clips:
        print("⚠️ No subtitle clips were generated! Check transcription output.")

    # Overlay subtitles on video
    final_video = CompositeVideoClip([video] + subtitle_clips)
    
    # Ensure final file format is compatible
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
