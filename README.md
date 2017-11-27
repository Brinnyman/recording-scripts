# Recording-scripts

## How To Use

To clone and run this application, you'll need [Git](https://git-scm.com), [Python3.5](https://www.python.org/downloads/release/python-350/), [FFmpeg](https://www.ffmpeg.org/) and [Streamlink](https://github.com/streamlink/streamlink) installed on your computer. From your command line:

```bash
# Clone this repository
$ git clone git@github.com:Brinnyman/recording-scripts

# Go into the repository
$ cd recording-scripts

# Install dependencies
$ pip install -r requirements.txt

# Configure the app
self.root_path = ''  # recording path
self.ffmpeg_path = ''  # path to ffmpeg executable
self.streamlink_path = ''  # path to streamlink executable

# Run the app
$ python3.5 recorder.py [options]
```

```bash
Options:
-h, --help    prints this message
-n, --name    recording directory and twitch username
-t, --type    recording type, default is twitch <twitch, youtube, vod, repair>
-u, --url     youtube-live url
-v, --vod     twitch vod id
-q, --quality recording quality, default is best <best, high, low, medium, mobile, source, worst>
-p, --path    recording path
-c, --command streamlink command
```

## Examples

```bash
Examples:
Recording twitch stream:
recorder.py -n username -t twitch -q best -c --twitch-disable-hosting
Recording twitch vod:
recorder.py -n username -t vod -v 13245678
Recording youtube stream:
recorder.py -n name -t youtube -u url -q 720p -p /recording
Repairing files in the recorded directory:
recorder.py -n name -t repair
```
