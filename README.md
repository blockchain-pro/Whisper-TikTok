# Introducing Whisper-TikTok 🤖🎥

Discover Whisper-TikTok, an innovative AI-powered tool that leverages the prowess of **Edge TTS**, **OpenAI-Whisper**, and **FFMPEG** to craft captivating TikTok videos. Harnessing the capabilities of OpenAI's Whisper model, Whisper-TikTok effortlessly generates an accurate **transcription** from provided audio files, laying the foundation for the creation of mesmerizing TikTok videos through the utilization of **FFMPEG**. Additionally, the program seamlessly integrates the **Microsoft Edge Cloud Text-to-Speech (TTS) API** to lend a vibrant **voiceover** to the video. Opting for Microsoft Edge Cloud TTS API's voiceover is a deliberate choice, as it delivers a remarkably **natural and authentic** auditory experience, setting it apart from the often monotonous and artificial voiceovers prevalent in numerous TikTok videos.

## Demo Video 🎬

<https://github.com/MatteoFasulo/Whisper-TikTok/assets/74818541/68e25504-c305-4144-bd39-c9acc218c3a4>

## Operating Principle

Employing Whisper-TikTok is a breeze: simply modify the [video.json](code/video.json). The JSON file contains the following fields:

- `series`: The name of the series.
- `part`: The part number of the video.
- `text`: The text to be spoken in the video.
- `outro`: The outro text to be spoken in the video.
- `path`: The path for saving subtitles files.

Summarizing the program's functionality:

> Furnished with a structured JSON dataset containing details such as the **series name**, **video part number**, **video text**, **outro text**, and **path**, the program orchestrates the synthesis of a video incorporating the provided text and outro. Subsequently, the generated video is stored within the designated `output` folder.

### In-Depth Insights

The program conducts the **sequence of actions** outlined below:

1. Retrieve **environment variables** from the optional .env file.
2. Validate the presence of **PyTorch** with **CUDA** installation. If the requisite dependencies are **absent**, the **program will use the CPU instead of the GPU**.
3. Download a random video from platforms like YouTube, e.g., a Minecraft parkour gameplay clip.
4. Load the OpenAI Whisper model into memory.
5. Extract the video text from the provided JSON file and initiate a **Text-to-Speech** request to the Microsoft Edge Cloud TTS API, preserving the response as an .mp3 audio file.
6. Utilize the OpenAI Whisper model to generate a detailed **transcription** of the .mp3 file, available in both .srt and .ass formats.
7. Select a **random background** video from the dedicated folder.
8. Integrate the srt and ass files into the chosen video using FFMPEG, creating a final .mp4 output.
9. Voila! In a matter of minutes, you've crafted a captivating TikTok video while sipping your favorite coffee ☕️.

## Prerequisites 🛠️

Whisper-TikTok has undergone rigorous testing on Windows 10 systems equipped with Python versions 3.8 and 3.9. To streamline the installation of necessary dependencies, execute the following command within your terminal:

```python
pip install -r requirements.txt
```

It also requires the command-line tool ffmpeg to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian

sudo apt update && sudo apt install ffmpeg

# on Arch Linux

sudo pacman -S ffmpeg

# on MacOS using Homebrew (<https://brew.sh/>)

brew install ffmpeg

# on Windows using Chocolatey (<https://chocolatey.org/>)

choco install ffmpeg

# on Windows using Scoop (<https://scoop.sh/>)

scoop install ffmpeg
```

Keep in mind that, due to the utilization of the OpenAI Whisper model for speech recognition, a GPU is recommended for optimal performance. However, the program will still function without a GPU, albeit at a slower pace.

## Usage Guidelines 📝

To embark on your Whisper-TikTok journey, initiate the following command within your terminal:

```bash
python main.py
```

## Command-Line Options

Whisper-TikTok supports the following command-line options:

```bash
python main.py [OPTIONS]

Options:
  --model TEXT        Model to use
                      [tiny|base|small|medium|large] (Default: small)
  --non_english       Don't use the English model. (Flag)
  --url TEXT          YouTube URL to download as background video.
                      (Default: <https://www.youtube.com/watch?v=intRX7BRA90>)
  --tts TEXT          Voice to use for TTS (Default: en-US-ChristopherNeural)
  --list-voices       Use `edge-tts --list-voices` to list all voices.
  --random_voice      Random voice for TTS (Flag)
  --gender TEXT       Gender of the random TTS voice [Male|Female].
  --language TEXT     Language of the random TTS voice
                      (e.g., en-US)
  -v, --verbose       Verbose (Flag)
```

> If you use the --random_voice option, please specify both --gender and --language arguments. Also you will need to specify the --non_english argument if you want to use a non-English voice otherwise the program will use the English model. Whisper model will auto-detect the language of the audio file and use the corresponding model.

## Usage Examples

- Generate a TikTok video using a specific TTS model and voice:

```bash
python main.py --model medium --tts en-US-EricNeural
```

- Generate a TikTok video without using the English model:

```bash
python main.py --non_english --tts de-DE-KillianNeural
```

- Use a custom YouTube video as the background video:

```bash
python main.py --url https://www.youtube.com/watch?v=dQw4w9WgXcQ --tts en-US-JennyNeural


python main.py --url https://www.youtube.com/watch?v=X7ZFuQS7rP0 --tts zh-CN-XiaoyiNeural


```

- Generate a TikTok video with a random TTS voice:

```bash
python main.py --random_voice --gender Male --language en-US

python main.py --url https://www.youtube.com/watch?v=X7ZFuQS7rP0  --random_voice --gender Male --language zh-CN


subtitles_translator -i NEW_INVENTIONS_THAT_WILL_SURPRISE_YOU-[X7ZFuQS7rP0].mp4 -o translated_video.mp4 -s en -t zh

subtitles_translator -i NEW_INVENTIONS_THAT_WILL_SURPRISE_YOU-[X7ZFuQS7rP0].srt -o translated.srt -s en -t zh

```

- List all available voices:

```bash
edge-tts --list-voices
```

## Code of Conduct

Please review our [Code of Conduct](./CODE_OF_CONDUCT.md) before contributing to Whisper-TikTok.

## Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](./CONTRIBUTING.md) for more information.

## Upcoming Features 🔮

- Integration with the OpenAI API to generate more advanced responses.
- Integration with the TikTok Developer API to upload videos directly to the platform.
- Improved user interface for a more seamless experience.

## OpenAI Whisper Forum Discussion

- <https://github.com/openai/whisper/discussions/223>

whisper NEW_INVENTIONS_THAT_WILL_SURPRISE_YOU-[X7ZFuQS7rP0].mp4 --language Chinese --task translate



## Acknowledgments

- We'd like to give a huge thanks to [@rany2](https://www.github.com/rany2) for their [edge-tts](https://github.com/rany2/edge-tts) package, which made it possible to use the Microsoft Edge Cloud TTS API with Whisper-TikTok.
- We also acknowledge the contributions of the Whisper model by [@OpenAI](https://github.com/openai/whisper) for robust speech recognition via large-scale weak supervision
