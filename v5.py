import openai
import os
import yt_dlp
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
import json
import re


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


# Fixing the trimming function
def trim_video_by_sentence(video_path, transcription, sentence_array):
    words = transcription.words
    segments = []
    last_end_time = 0.0

    for sentence in sentence_array:
        if sentence.strip():
            last_word = sentence.split()[-1]
            for i, word_info in enumerate(words):
                if word_info.word == last_word and word_info.start >= last_end_time:
                    start_time = words[i - len(sentence.split()) + 1].start
                    end_time = word_info.end
                    segments.append((start_time, end_time))
                    last_end_time = end_time
                    break

    # Trim each video segment without `with_audio`
    for idx, (start, end) in enumerate(segments):
        print(f"Trimming video from {start} to {end}")
        try:
            with VideoFileClip(video_path) as video:
                trimmed_clip = video.subclip(start, end)
                trimmed_clip_path = f"downloaded_videos/trimmed_segment_{idx + 1}.mp4"
                trimmed_clip.write_videofile(trimmed_clip_path, codec="libx264", verbose=True)
                print(f"Segment saved as {trimmed_clip_path}")
        except Exception as e:
            print(f"Error trimming segment {idx + 1}: {e}")


def segment_text(text):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a sentence segmenter that outputs JSON"},
            {"role": "user", "content": f"Segment the following text into 30-60s chunks, outputting a JSON list of sentences only: {text}"}
        ]
    )
    response_text = completion.choices[0].message.content
    # Remove code block characters for JSON parsing
    response_text = re.sub(r'```json|```', '', response_text).strip()
    try:
        sentence_array = json.loads(response_text)
        print("Segmented sentences:", sentence_array)
        return sentence_array
    except json.JSONDecodeError:
        print("Failed to parse sentence array as JSON:", response_text)
        return []


#Providing the path to the video
video_path = download_youtube_video("https://www.youtube.com/watch?v=4cLVN_6cGew&t=2s")

#Converting Video to Audio
mp3_path = convert_mp4_to_mp3(video_path)
print("Successfully converted to mp3, the mp3_path is -", mp3_path)

#Creating transcription for Audio
transcription = speech_to_text(mp3_path)
print("Transcription Received")
        
#Creating Sentence Array
sentence_array = segment_text(transcription.text)

#Trimming Audio based on Transcription and Sentence Array
trim_video_by_sentence(video_path, transcription, sentence_array)
print("Video trimmed Successfully")
