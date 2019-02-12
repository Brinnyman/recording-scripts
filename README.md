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
self.recordpath = ''  # recording path
self.ffmpeg_path = ''  # path to ffmpeg executable
self.streamlink_path = ''  # path to streamlink executable

# Run the app
$ python recorder.py [options]
```

```bash
Options:
-h, --help        prints this message
-n, --name        recording directory and twitch username
-t, --type        recording type <twitch, vod>
-u, --url         url
-v, --vod         twitch vod id
-q, --quality     recording quality, first that is available <720p, 720p60, 1080p, 1080p60>. You can override these by providing the quality or pick the default Streamlink settings <best> or <worst>.
-r, --recordpath  recordpath
-c, --command     streamlink command
```

## Examples

```bash
Examples:
Recording stream:
recorder.py -n name -u url -r /recordpath
recorder.py -n name -u url -q 720p -r /recordpath
recorder.py -n name -u url -q best -r /recordpath
Recording twitch stream:
recorder.py -n username -t twitch -c --twitch-disable-hosting
recorder.py -n username -t twitch -q 1080p60 -c --twitch-disable-hosting
recorder.py -n username -t twitch -q best -c --twitch-disable-hosting
Recording twitch vod:
recorder.py -n username -t vod -v 13245678
```
