import os
import getopt
import sys
import requests
import datetime
import subprocess
import time
import configparser

class StreamRecorder:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.refresh = int(config['SETUP']['REFRESH_RATE'])
        self.name = config['SETUP']['NAME']
        self.type = config['SETUP']['TYPE']
        self.url = config['SETUP']['URL']
        self.recordpath = config['SETUP']['RECORD_PATH']
        self.streamlink_path = config['STREAMLINK']['STREAMLINK_PATH']
        self.quality = config['STREAMLINK']['STREAMLINK_QUALITY']
        self.streamlink_commands = config['STREAMLINK']['STREAMLINK_COMMANDS']
        self.ffmpeg_path = config['FFMPEG']['FFMPEG_PATH']
        self.twitch_client_id = config['TWITCH']['TWITCH_CLIENT_ID']
        self.vodid = config['TWITCH']['VOD_ID']

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

    def record(self, url, filename, *args):
        process = None

        try:
            print('Recording in session.')
            
            print('start streamlink')
            streamlink = [self.streamlink_path, url, self.quality, '--stdout'] + list(args)
            print(streamlink)
            process = subprocess.Popen(streamlink, stdout=subprocess.PIPE, stderr=None)

            print('start ffmpeg')
            ffmpeg = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', 'pipe:0', '-c', 'copy', filename, '-loglevel', 'quiet']
            print(ffmpeg)
            process2 = subprocess.Popen(ffmpeg, stdin=process.stdout, stdout=subprocess.PIPE, stderr=None)

            process.stdout.close()
            process2.communicate()
            print('Recording is done.')

        except OSError:
            print('An error has occurred while trying to use livestreamer package. Is it installed? Do you have Python in your PATH variable?')
            sys.exit(1)

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
        print('check channel {0} stream status'.format(self.name))
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
    usage += '-q, --quality     recording quality, first that is available <720p, 720p60, 1080p, 1080p60, best>. You can override these by providing the quality or pick the default Streamlink settings <best> or <worst>.\n'
    usage += '-r, --recordpath  recordpath\n'
    usage += '-c, --command     streamlink command\n'
    usage += '\n'
    usage += 'Examples:\n'
    usage += 'Recording stream:\nrecorder.py -n name -u url -r /recordpath\n'
    usage += 'recorder.py -n name -u url -r /recordpath\n'
    usage += 'recorder.py -n name -u url -q 720p -r /recordpath\n'
    usage += 'recorder.py -n name -u url -q best -r /recordpath\n\n'
    usage += 'Recording twitch stream:\n'
    usage += 'recorder.py -n username -t twitch -c --twitch-disable-hosting\n'
    usage += 'recorder.py -n username -t twitch -q 1080p60 -c --twitch-disable-hosting\n'
    usage += 'recorder.py -n username -t twitch -q best -c --twitch-disable-hosting\n\n'
    usage += 'Recording twitch vod:\n'
    usage += 'recorder.py -n username -t vod -v 13245678\n'

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

if __name__ == "__main__":
    main(sys.argv[1:])