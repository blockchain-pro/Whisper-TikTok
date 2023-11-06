import platform
import os
from pathlib import Path
import random
import re
import json
import sys
import subprocess
import asyncio
import multiprocessing
import logging
from typing import Tuple
import datetime
import argparse

# PyTorch
import torch

# ENV
from dotenv import load_dotenv, find_dotenv

# OpenAI Whisper Model PyTorch
import whisper

# MicrosoftEdge TTS
import edge_tts

# FFMPEG (Python)
import ffmpeg

# utils.py
from utils import *

# msg.py
import msg

# Default directory
HOME = os.getcwd()

# Logging
if not os.path.isdir('log'):
    os.mkdir('log')

with KeepDir() as keep_dir:
    keep_dir.chdir("log")
    log_filename = f'{datetime.date.today()}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
        ]
    )
    logger = logging.getLogger(__name__)


###########################
#        VIDEO.JSON       #
###########################

jsonData = json.load(open('video.json', encoding='utf-8'))


#######################
#         CODE        #
#######################


async def main() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="small", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"], type=str)
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--url", metavar='U', default="https://www.youtube.com/watch?v=intRX7BRA90",
                        help="Youtube URL to download as background video.", type=str)
    parser.add_argument("--tts", default="en-US-ChristopherNeural",
                        help="Voice to use for TTS", type=str)
    parser.add_argument(
        "--list-voices", help="Use `edge-tts --list-voices` to list all voices", action='help')
    parser.add_argument("--random_voice", action='store_true',
                        help="Random voice for TTS", default=False)
    parser.add_argument("--gender", choices=["Male", "Female"],
                        help="Gender of the random TTS voice", type=str)
    parser.add_argument(
        "--language", help="Language of the random TTS voice for example: en-US", type=str)
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Verbose")
    args = parser.parse_args()

    if args.random_voice: # Random voice
        args.tts = None
        if not args.gender or not args.language:
            console.log(
                f"{msg.ERROR}When using --random_voice, please specify both --gender and --language arguments.")
            sys.exit(1)

        else: # Check if language is valid
            voices = await edge_tts.VoicesManager.create()
            voices = voices.find(Gender=args.gender, Locale=args.language)
            if len(voices) == 0:
                # Locale not found
                console.log(
                    f"{msg.ERROR}Specified TTS language not found. Make sure you are using the correct format. For example: en-US")
                sys.exit(1)

            # Check if language is english
            if not str(args.language).startswith('en'):
                args.non_english = True

    # Clear terminal
    console.clear()

    logger.debug('Creating video')
    with console.status(msg.STATUS) as status:
        load_dotenv(find_dotenv())  # Optional

        console.log(
            f"{msg.OK}Finish loading environment variables")
        logger.info('Finish loading environment variables')

        # Check if GPU is available for PyTorch (CUDA).
        if torch.cuda.is_available():
            console.log(f"{msg.OK}PyTorch GPU version found")
            logger.info('PyTorch GPU version found')
        else:
            console.log(
                f"{msg.WARNING}PyTorch GPU not found, using CPU instead")
            logger.warning('PyTorch GPU not found')

        download_video(url=args.url)

        # OpenAI-Whisper Model
        model = args.model
        if args.model != "large" and not args.non_english:
            model = args.model + ".en"
        whisper_model = whisper.load_model(model)

        console.log(f"{msg.OK}OpenAI-Whisper model loaded")
        logger.info('OpenAI-Whisper model loaded')

        # Text 2 Speech (Edge TTS API)
        for video_id, video in enumerate(jsonData):
            series = video['series']
            part = video['part']
            outro = video['outro']
            path = video['path']
            text = video['text']

            req_text, filename = create_full_text(
                path, series, part, text, outro)

            console.log(f"{msg.OK}Text converted successfully")
            logger.info('Text converted successfully')
            console.log(req_text)
            await tts(req_text, outfile=filename, voice=args.tts, random_voice=args.random_voice, args=args)

            console.log(
                f"{msg.OK}Text2Speech mp3 file generated successfully!")
            logger.info('Text2Speech mp3 file generated successfully!')

            # Whisper Model to create SRT file from Speech recording
            srt_filename = srt_create(
                whisper_model, path, series, part, text, filename)

            console.log(
                f"{msg.OK}Transcription srt and ass file saved successfully!")
            logger.info('Transcription srt and ass file saved successfully!')

            # Background video with srt and duration
            background_mp4 = random_background()
            file_info = get_info(background_mp4, verbose=args.verbose)
            final_video = prepare_background(
                background_mp4, filename_mp3=filename, filename_srt=srt_filename, duration=int(file_info.get('duration')), verbose=args.verbose)
            console.log(
                f"{msg.OK}MP4 video saved successfully!\nPath: {final_video}")
            logger.info(f'MP4 video saved successfully!\nPath: {final_video}')

    console.log(f'{msg.DONE}')
    return True

def download_video(url: str, folder: str = 'background'):
    """
    Downloads a video from the given URL and saves it to the specified folder.

    Args:
        url (str): The URL of the video to download.
        folder (str, optional): The name of the folder to save the video in. Defaults to 'background'.
    """
    if not os.path.isdir(folder):
        os.mkdir(f"{HOME}{os.sep}{folder}")
    with KeepDir() as keep_dir:
        keep_dir.chdir(folder)
        with subprocess.Popen(['yt-dlp', '--restrict-filenames', '--merge-output-format', 'mp4', url]) as process:
            pass
        console.log(
            f"{msg.OK}Background video downloaded successfully")
        logger.info('Background video downloaded successfully')
    return

def random_background(folder_path: str = "background") -> str:
    """
    Returns the filename of a random file in the specified folder path.
    
    Args:
        folder_path (str): The path to the folder containing the files.
        
    Returns:
        str: The filename of a randomly selected file in the folder.
    """
    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)
    with KeepDir() as keep_dir:
        keep_dir.chdir(f"{HOME}{os.sep}{folder_path}")
        files = os.listdir(".")
        random_file = random.choice(files)
    return random_file


def get_info(filename: str, verbose: bool = False):
    """
    Get information about a video file.

    Args:
        filename (str): The path to the video file.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        dict: A dictionary containing information about the video file, including width, height, bit rate, and duration.
    """
    try:
        with KeepDir() as keep_dir:
            keep_dir.chdir(f"{HOME}{os.sep}background")

            # Get video duration
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            duration = float(result.stdout)

            try:
                # Get video width and height
                result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'default=noprint_wrappers=1:nokey=1', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                width_height = result.stdout.decode('utf-8').strip().split('\n')
                width, height = width_height[0], width_height[1]

            except IndexError: # audio stream
                result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=bit_rate', '-of', 'default=noprint_wrappers=1:nokey=1', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                bit_rate = result.stdout.decode('utf-8').strip()
                return {'bit_rate': bit_rate, 'duration': duration}

            return {'width': int(width), 'height': int(height), 'duration': duration}
    except ffmpeg.Error as e:
        console.log(f"{msg.ERROR}{e.stderr}")
        logger.exception(e.stderr)
        sys.exit(1)

def prepare_background(background_mp4: str, filename_mp3: str, filename_srt: str, duration: int, verbose: bool = False) -> str:
    """
    Prepare a background video with an audio file and a subtitle file.

    Args:
        background_mp4 (str): The path to the background video file.
        filename_mp3 (str): The path to the audio file to be merged with the background video.
        filename_srt (str): The path to the subtitle file to be added to the background video.
        duration (int): The duration of the output video in seconds.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        str: The path to the output video file.
    """
    # Get length of MP3 file to be merged with
    audio_info = get_info(filename_mp3)

    # Get starting time:
    audio_duration = int(round(audio_info.get('duration'), 0))
    ss = random.randint(0, (duration-audio_duration))
    audio_duration = convert_time(audio_info.get('duration'))
    if ss < 0:
        ss = 0

    srt_filename = filename_srt.split('\\')[-1]
    srt_path = Path(srt_filename).parent.absolute()

    # Create output directory
    if not os.path.isdir(f"{HOME}{os.sep}output"):
        os.mkdir(f"{HOME}{os.sep}output")
    outfile = f"{HOME}{os.sep}output{os.sep}output_{ss}.mp4"

    with KeepDir() as keep_dir:
        keep_dir.chdir(f"{HOME}{os.sep}background")
        mp4_absolute_path = os.path.abspath(background_mp4)

    if verbose:
        rich_print(
            f"{filename_srt = }\n{mp4_absolute_path = }\n{filename_mp3 = }\n", style='bold green')   #
        # 'Alignment=9,BorderStyle=3,Outline=5,Shadow=3,Fontsize=15,MarginL=5,MarginV=25,FontName=Lexend Bold,ShadowX=-7.1,ShadowY=7.1,ShadowColour=&HFF000000,Blur=141'Outline=5
    args = [
        "ffmpeg", 
        "-ss", str(ss), 
        "-t", str(audio_duration), 
        "-i", mp4_absolute_path, 
        "-i", filename_mp3, 
        "-map", "0:v", 
        "-map", "1:a", 
        "-filter:v", 
        f"crop=ih/16*9:ih, scale=w=1080:h=1920:flags=bicubic, gblur=sigma=2, subtitles={srt_filename}:force_style=',Alignment=8,BorderStyle=7,Outline=3,Shadow=5,Blur=15,Fontsize=15,MarginL=45,MarginR=55,FontName=Lexend Bold'", 
        "-c:v", "libx264", "-preset", "5", 
        "-b:v", "5M", 
        "-c:a", "aac", "-ac", "1", 
        "-b:a", "96K", 
        f"{outfile}", "-y", 
        "-threads", f"{multiprocessing.cpu_count()//2}"]

    if verbose:
        rich_print('[i] FFMPEG Command:\n'+' '.join(args)+'\n', style='yellow')

    with KeepDir() as keep_dir:
        keep_dir.chdir(srt_path)
        with subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
            pass

    return outfile

def srt_create(model, path: str, series: str, part: int, text: str, filename: str) -> bool:
    """
    Create an SRT file for a given video file using the specified model.

    Args:
        model: The model to use for transcription.
        path (str): The path to the directory where the SRT file should be saved.
        series (str): The name of the series the video belongs to.
        part (int): The part number of the video.
        text (str): The text to transcribe.
        filename (str): The name of the video file.

    Returns:
        bool: True if the SRT file was created successfully, False otherwise.
    """
    series = series.replace(' ', '_')
    srt_path = f"{path}{os.sep}{series}{os.sep}"

    word_options = {
        "highlight_words": True,
        "max_line_count": 1,
        "max_line_width": 40,
        "preserve_segments": False,
    }

    transcribe = model.transcribe(
        filename, task="transcribe", word_timestamps=True, fp16=torch.cuda.is_available())
    vtt_writer = whisper.utils.get_writer(
        output_format="srt", output_dir=srt_path)
    vtt_writer(transcribe, filename, word_options)

    srt_filename = f"{srt_path}{series}_{part}.srt"

    return srt_filename


def convert_time(time_in_seconds):
    """
    Converts time in seconds to a string in the format "hh:mm:ss.mmm".

    Args:
        time_in_seconds (float): The time in seconds to be converted.

    Returns:
        str: The time in the format "hh:mm:ss.mmm".
    """
    hours = int(time_in_seconds // 3600)
    minutes = int((time_in_seconds % 3600) // 60)
    seconds = int(time_in_seconds % 60)
    milliseconds = int((time_in_seconds - int(time_in_seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def batch_create(filename: str) -> None:
    """
    Batch creates a file by concatenating all files in the './batch/' directory in alphanumeric order.

    Args:
    - filename (str): the name of the file to be created.

    Returns:
    - None
    """
    with open(filename, 'wb') as out:
        def sorted_alphanumeric(data):
            def convert(text): return int(
                text) if text.isdigit() else text.lower()
            def alphanum_key(key): return [convert(c)
                                           for c in re.split('([0-9]+)', key)]
            return sorted(data, key=alphanum_key)

        for item in sorted_alphanumeric(os.listdir('./batch/')):
            filestuff = open('./batch/' + item, 'rb').read()
            out.write(filestuff)

def create_full_text(path: str = '', series: str = '', part: int = 1, text: str = '', outro: str = '') -> Tuple[str, str]:
    """
    Creates full text and filename for a given series, part, text and outro.

    Args:
        path (str): The path where the file will be saved.
        series (str): The name of the series.
        part (int): The part number of the series.
        text (str): The main text of the series.
        outro (str): The outro of the series.

    Returns:
        Tuple[str, str]: A tuple containing the full text and filename.
    """
    req_text = f"{series} Part {part}.\n{text}\n{outro}"
    series = series.replace(' ', '_')
    filename = f"{path}{os.sep}{series}{os.sep}{series}_{part}.mp3"
    
    # create directory if not exist
    if not os.path.isdir(f"{path}{os.sep}{series}"):
        os.mkdir(f"{path}{os.sep}{series}")
    return req_text, filename


async def tts(final_text: str, voice: str = "en-US-ChristopherNeural", random_voice: bool = False, stdout: bool = False, outfile: str = "tts.mp3", args=None) -> bool:
    """
    Converts text to speech using Microsoft Edge Text-to-Speech API.

    Args:
        final_text (str): The text to be converted to speech.
        voice (str, optional): The name of the voice to use. Defaults to "en-US-ChristopherNeural".
        random_voice (bool, optional): Whether to choose a random voice based on the gender and language specified in `args`. Defaults to False.
        stdout (bool, optional): Whether to output the speech audio to stdout. Defaults to False.
        outfile (str, optional): The name of the output file. Defaults to "tts.mp3".
        args (object, optional): An object containing the gender and language to use when selecting a random voice. Defaults to None.

    Returns:
        bool: True if the text was successfully converted to speech and saved to a file, False otherwise.
    """
    voices = await edge_tts.VoicesManager.create()
    if random_voice:
        voices = voices.find(Gender=args.gender, Locale=args.language)
        voice = random.choice(voices)["Name"]
    communicate = edge_tts.Communicate(final_text, voice)
    if not stdout:
        await communicate.save(outfile)
    return True

if __name__ == "__main__":

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())

    except Exception as e:
        loop.close()
        console.log(f"{msg.ERROR}{e}")
        logger.exception(e)

    finally:
        loop.close()

    sys.exit(1)
