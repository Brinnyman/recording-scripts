import os
import getopt
import sys
import requests
import datetime
import subprocess
import time


class StreamRecorder:
    def __init__(self):
        self.twitch_client_id = "jzkbprff40iqj646a697cyrvl0zt2m6"  # don't change this TODO: Maybe change this because everybody uses this ID
        self.refresh = 15.0
        self.name = ""  # recording directory and twitch username
        self.type = ""  # recording type <twitch, vod, repair>
        self.url = ""  # url
        self.vodid = ""  # twitch vod id
        self.quality = "720p, 720p60, 1080p, 1080p60"  # recording quality, first that is available <720p, 720p60, 1080p, 1080p60>. You can override these by providing the quality or pick the default streamlink settings <best> or <worst>.
        self.recordpath = ""  # record path
        self.streamlink_commands = ""  # streamlink commands
        self.ffmpeg_path = 'ffmpeg'  # path to ffmpeg executable
        self.streamlink_path = 'streamlink'  # path to streamlink executable

    def create_directory(self):
        self.recorded_path = os.path.join(os.path.abspath(self.recordpath), "recorded", self.name)
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)

        if(self.refresh < 15):
            print("Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print("System set check interval to 15 seconds.")

    def create_filename(self, name, date):
        filename = name + "_" + date + ".mp4"
        filename = "".join(x for x in filename if x.isalnum() or x in ["-", "_", "."])
        filename = os.path.join(self.recorded_path, filename)
        return filename

	# Streamlink pipes the stream data as input to the ffmpeg subprocess. Ffmpeg compresses the data to an mp4 file.
	# When a stream goes offline, it gives an pipe error. Because the status still says the stream is online. Streamlink then gives and error that no playable stream is found. subprocess.CalledProcessError?
	# Thus ffmpeg cant create a new file. Takes over 1min to finally show the status as offline. The actual stream is also still playing for a couple of seconds after the stream is stopped.

	# It does take 1min to start the recording again. That is because of the status check. Also happends with the old script

    def record(self, url, filename, *args):
        process = None

        try:
            print('Recording in session.')
            
            print('start streamlink')
            streamlink = [self.streamlink_path, url, self.quality, '--stdout'] + list(args)
            print(streamlink)
            process = subprocess.Popen(streamlink, stdout=subprocess.PIPE, stderr=None)

            print('start ffmpeg')
            # TODO: Test with -bsf h264_mp4toannexb
            # ffmpeg = [self.ffmpeg_path, '-i', 'pipe:0', '-bsf', 'h264_mp4toannexb', '-vcodec', 'libx264', '-acodec', 'aac', '-f', 'mpegts', filename]
            # h26_mp4toannexb doesn't support aac

            # TODO: Test with original parameters using the streamlink pipe
            # Recording worked. Did give a message [stream.hls][warning] Failed to reload playlist: Unable to open URL: 
            # Don't know what that is about.
            ffmpeg = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', 'pipe:0', '-c', 'copy', filename, '-loglevel', 'quiet']
            print(ffmpeg)
            process2 = subprocess.Popen(ffmpeg, stdin=process.stdout, stdout=subprocess.PIPE, stderr=None)

            # TODO: Have to checkout what this does and if i need to close the second process.
            process.stdout.close()
            process2.communicate()
            print('Recording is done.')

        except OSError:
            print('An error has occurred while trying to use livestreamer package. Is it installed? Do you have Python in your PATH variable?')
            sys.exit(1)

        # TODO: remove stdout?
        return process2.stdout

    def run(self):
        print('Start StreamRecorder')
        self.create_directory()

        if self.type == 'twitch':
            self.record_twitch_stream()
        elif self.type == 'vod':
            self.record_twitch_vod()
        else:
            self.record_stream()

    def check_twitch_stream_status(self):
        api = 'https://api.twitch.tv/kraken/streams/' + self.name
        info = None
        status = 3  # 3: error
        try:
            r = requests.get(api, headers={"Client-ID": self.twitch_client_id}, timeout=15)
            r.raise_for_status()
            info = r.json()
            if info['stream'] is None:
                status = 0
            elif info['stream']['stream_type'] == 'live':		
                status = 1
        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.reason == 'Not Found' or e.response.reason == 'Unprocessable Entity':
                    print("stream not found")
                    status = 2  # 2: not found
        return status

    def check_twitch_vod(self):
        api = 'https://api.twitch.tv/kraken/videos/' + self.vodid
        info = None
        r = requests.get(api, headers={"Client-ID": self.twitch_client_id}, timeout=15)
        r.raise_for_status()
        info = r.json()
        return info

    def record_twitch_stream(self):
        self.streamlink_commands = "--twitch-disable-hosting"
        print('check twitch stream status')
        while True:
            status = self.check_twitch_stream_status()
            if status == 1:
                print(self.name, "online.")
                recorded_filename = self.create_filename(self.name, datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss"))
                self.url = 'twitch.tv/' + self.name
                self.record(self.url, recorded_filename, self.streamlink_commands)
            
            time.sleep(self.refresh)

    def record_twitch_vod(self):
        info = self.check_twitch_vod()
        filename = self.create_filename(info['channel']['name'], info['published_at'])
        self.url = 'twitch.tv/videos/' + self.vodid
        self.record(self.url, filename)

    def record_stream(self):
        while True:
            filename = self.create_filename(self.name, datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss"))
            self.record(self.url, filename)
            time.sleep(self.refresh)


def main(argv):
    """Exectute command line options."""
    recorder = StreamRecorder()

    usage = 'Usage: recorder.py [options]\n'
    usage += '\n'
    usage += 'Options:\n'
    usage += '-h, --help        prints this message\n'
    usage += '-n, --name        recording directory and twitch username\n'
    usage += '-t, --type        recording type <twitch, vod>\n'
    usage += '-u, --url         url\n'
    usage += '-v, --vod         twitch vod id\n'
    usage += '-q, --quality     recording quality, first that is available <720p, 720p60, 1080p, 1080p60>. You can override these by providing the quality or pick the default Streamlink settings <best> or <worst>.\n'
    usage += '-r, --recordpath  recordpath\n'
    usage += '-c, --command     streamlink command\n'
    usage += '\n'
    usage += 'Examples:\n'
    usage += 'Recording stream: recorder.py -n name -u url -r /recordpath\n'
    usage += 'Recording stream: recorder.py -n name -u url -q 720p -r /recordpath\n'
    usage += 'Recording stream: recorder.py -n name -u url -q best -r /recordpath\n'
    usage += 'Recording twitch stream:\nrecorder.py -n username -t twitch -c --twitch-disable-hosting\n'
    usage += 'Recording twitch stream:\nrecorder.py -n username -t twitch -q 1080p60 -c --twitch-disable-hosting\n'
    usage += 'Recording twitch stream:\nrecorder.py -n username -t twitch -q best -c --twitch-disable-hosting\n'
    usage += 'Recording twitch vod:\nrecorder.py -n username -t vod -v 13245678\n'

    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'hn:u:t:v:q:r:p:c:', ['name=',
                                                                               'url=',
                                                                               'type=',
                                                                               'vod=',
                                                                               'quality=',
                                                                               'recordpath=',
                                                                               'command='])
    except getopt.GetoptError as e:
        print(usage)
        sys.exit(2)

    for opt, arg in options:
        if opt == '-h':
            print(usage)
            sys.exit()
        elif opt in ('-n', '--name'):
            recorder.name = arg
        elif opt in ('-u', '--url'):
            recorder.url = arg
        elif opt in ('-t', '--type'):
            recorder.type = arg
        elif opt in ('-v', '--vod'):
            recorder.vodid = arg
        elif opt in ('-q', '--quality'):
            recorder.quality = arg
        elif opt in ('-r', '--recordpath'):
            recorder.recordpath = arg
        elif opt in ('-c', '--command'):
            recorder.command = arg

    recorder.run()

# TODO: need a way to stop the program
# TODO: would be cool to have a program as controlpanel that opens up a second 'terminal' to run the recording.
# TODO: or streamlink writes to a file and after its done a second program start to process the file with ffmpeg. And let the streamlink program continue with its loop.

if __name__ == "__main__":
    main(sys.argv[1:])