import openai
import os
import yt_dlp
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip

# API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=openai_api_key)


def speech_to_text(mp3_path):
    audio_file = open(mp3_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format='verbose_json',
        timestamp_granularities=['word']
    )
    print("The transciption text is", transcription.text)
    return transcription  # Return the full transcription for further processing


def download_youtube_video(url):
    output_folder = "downloaded_videos"
    
    # Ensure the output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get("title", None)
            video_path = os.path.join(output_folder, f"{video_title}.mp4")
            print(f"Video downloaded successfully: {video_path}")
            return video_path
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

def convert_mp4_to_mp3(video_path):
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    mp3_path = os.path.join("downloaded_videos", f"{file_name}.mp3")
    
    try:
        audio = AudioSegment.from_file(video_path, format="mp4")
        audio.export(mp3_path, format="mp3")
        print(f"Conversion successful! Saved as {mp3_path}")
        return mp3_path
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return None


def trim_video_by_sentence(video_path, transcription, sentence_array):
    """
    Trim the video into segments based on sentence boundaries.
    
    Parameters:
    - video_path: The path of the downloaded video file.
    - transcription: Transcription with word-level timestamps.
    - sentence_array: Array of sentences from the transcription.
    
    """
    # Initialize variables
    words = transcription.words
    segments = []
    last_end_time = 0.0  # Track the end time of previous sentences to begin search

    for sentence in sentence_array:
        # Get the last word of the current sentence
        last_word = sentence.split()[-1]
        
        # Find the last occurrence of the word after `last_end_time`
        for i, word_info in enumerate(words):
            if word_info.word == last_word and word_info.start >= last_end_time:
                # Found the end of the sentence, save the start and end times for the sentence
                start_time = words[i - len(sentence.split()) + 1].start  # Approximate start of sentence
                end_time = word_info.end
                segments.append((start_time, end_time))
                last_end_time = end_time  # Update last_end_time to this segment's end
                break

    # Trim the video for each sentence segment
    for idx, (start, end) in enumerate(segments):
        print(f"Trimming video from {start} to {end}")  # Debugging print for start and end times
        try:
            with VideoFileClip(video_path) as video:
                trimmed_clip = video.subclip(start, end).with_audio(True)
                trimmed_clip_path = f"downloaded_videos/trimmed_segment_{idx + 1}.mp4"
                trimmed_clip.write_videofile(trimmed_clip_path, codec="libx264", verbose=True)
                print(f"Segment saved as {trimmed_clip_path}")
        except Exception as e:
            print(f"Error trimming segment {idx + 1}: {e}")


# Example usage:
video_path = download_youtube_video("https://www.youtube.com/watch?v=4cLVN_6cGew&t=2s")
if video_path:
    mp3_path = convert_mp4_to_mp3(video_path)
    print("Successfully converted to mp3, the mp3_path is -", mp3_path)
    if mp3_path:
        transcription = speech_to_text(mp3_path)
        print("Transcription Received")
        
        # Example sentence array (split based on desired duration, using OpenAI API or custom logic)
        sentence_array = [
        "When you grab your phone, it's time to explode",
        "Check out the app, that's breaking down doors",
        "Custom images of yourself, that's your stuff",
        "Swipe, swipe, focus, you're worth a dollar",
        "Draw the inner bottles, alter it from your feet"]

        
        trim_video_by_sentence(video_path, transcription, sentence_array)
        print("Video trimmed Successfully")
