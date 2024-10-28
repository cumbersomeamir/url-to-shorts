import openai
import os
import yt_dlp
from pydub import AudioSegment



# API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=openai_api_key)



def speech_to_text():

    audio_file= open("/Users/amir/Desktop/opus/lib/python3.12/site-packages/sample-audio.mp3", "rb")
    transcription = client.audio.transcriptions.create(
      model="whisper-1",
      file=audio_file
    )
    print(transcription.text)

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
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

# Example usage:
video_path = download_youtube_video("https://www.youtube.com/watch?v=4cLVN_6cGew&t=2s")
if video_path:
    convert_mp4_to_mp3(video_path)
