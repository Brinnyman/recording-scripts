import os
import getopt
import sys
import requests
import datetime
import subprocess
import time


class Recorder:
    def __init__(self):
        self.twitch_client_id = "jzkbprff40iqj646a697cyrvl0zt2m6"  # don't change this
        self.refresh = 15.0
        self.name = ""  # recording directory and twitch username
        self.type = "twitch"  # recording type, default is twitch <twitch, youtube, vod, repair>
        self.url = ""  # youtube-live-url
        self.vodid = ""  # twitch vod id
        self.quality = "best"  # recording quality, default is best <best, high, low, medium, mobile, source, worst>
        self.root_path = ""  # recording path
        self.command = ""  # streamlink commands
        self.ffmpeg_path = 'ffmpeg'  # path to ffmpeg executable
        self.streamlink_path = 'streamlink'  # path to streamlink executable

    def setup(self):
        self.recorded_path = os.path.join(os.path.abspath(self.root_path), "recorded", self.name)
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        self.processed_path = os.path.join(os.path.abspath(self.root_path), "processed", self.name)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        if(self.refresh < 15):
            print("Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print("System set check interval to 15 seconds.")

    def create_files(self, name, date):
        filename = name + "_" + date + ".mp4"
        filename = "".join(x for x in filename if x.isalnum() or x in ["-", "_", "."])
        recorded_filename = os.path.join(self.recorded_path, filename)
        processed_filename = os.path.join(self.processed_path, filename)
        return recorded_filename, processed_filename

    def clean_files(self, recorded_filename, processed_filename):
        print('Check if recorded file needs to be repaired.')
        if(os.path.exists(recorded_filename) is True):
            try:
                print("Repair video file.")
                subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', processed_filename])
                print("Repaired video file.")
                os.remove(recorded_filename)
            except Exception as e:
                print(e)
        else:
            print("Skip repairing. File not found.")

    def record(self, url, filename, *args):
        print("Recording in session.")
        print(self.streamlink_path, url, self.quality, "-o", filename, list(args))
        subprocess.call([self.streamlink_path, url, self.quality, "-o", filename] + list(args))
        print("Recording is done.")

    def run(self):
        self.setup()
        print('Start recorder')

        try:
            print('Check if there are files in the recorded folder.')
            video_list = [f for f in os.listdir(self.recorded_path) if os.path.isfile(os.path.join(self.recorded_path, f))]
            if(len(video_list) > 0):
                print('Repairing previously recorded files.')
            for f in video_list:
                recorded_filename = os.path.join(self.recorded_path, f)
                processed_filename = os.path.join(self.processed_path, f)
                if(os.path.exists(recorded_filename) is True):
                    self.clean_files(recorded_filename, processed_filename)
                else:
                    print("Skip repairing. File not found.")
        except Exception as e:
            print(e)

        if self.type == 'repair':
            return
        elif self.type == 'twitch':
            self.record_twitch_stream()
        elif self.type == 'vod':
            self.record_twitch_vod()
        elif self.type == 'youtube':
            self.record_youtube_stream()
        else:
            return

    def check_twitch_stream(self):
        api = 'https://api.twitch.tv/kraken/streams/' + self.name
        info = None
        status = 3  # 3: error
        try:
            r = requests.get(api, headers={"Client-ID": self.twitch_client_id}, timeout=15)
            r.raise_for_status()
            info = r.json()
            if info['stream'] is None:
                status = 1  # 1: offline
            elif info['stream']['stream_type'] == 'watch_party':
                status = 4  # 4: vodcast
            else:
                status = 0  # 0: online
        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.reason == 'Not Found' or e.response.reason == 'Unprocessable Entity':
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
        self.command = "--twitch-disable-hosting"
        while True:
            status = self.check_twitch_stream()
            if status == 2:
                print("Stream not found. Invalid stream or typo.")
                time.sleep(self.refresh)
            elif status == 3:
                print(datetime.datetime.now().strftime("%Hh%Mm%Ss"), " ", "unexpected error. will try again in 5 minutes.")
                time.sleep(300)
            elif status == 4:
                print(self.name, "currently vodcasting, checking again in", self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 1:
                print(self.name, "currently offline, checking again in", self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 0:
                print(self.name, "online. Stream recording in session.")

                recorded_filename, processed_filename = self.create_files(self.name, datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss"))
                self.url = 'twitch.tv/' + self.name
                self.record(self.url, recorded_filename, self.command)
                self.clean_files(recorded_filename, processed_filename)

                time.sleep(self.refresh)

    def record_twitch_vod(self):
        info = self.check_twitch_vod()
        recorded_filename, processed_filename = self.create_files(info['channel']['name'], info['published_at'])
        self.url = 'twitch.tv/videos/' + self.vodid
        self.record(self.url, recorded_filename)
        self.clean_files(recorded_filename, processed_filename)

    def record_youtube_stream(self):
        while True:
            recorded_filename, processed_filename = self.create_files('_' + self.name, datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss"))
            self.record(self.url, recorded_filename)
            self.clean_files(recorded_filename, processed_filename)
            time.sleep(self.refresh)


def main(argv):
    """Exectute command line options."""
    recorder = Recorder()

    usage = 'Usage: recorder.py [options]\n'
    usage += '\n'
    usage += 'Options:\n'
    usage += '-h, --help    prints this message\n'
    usage += '-n, --name    recording directory and twitch username\n'
    usage += '-t, --type    recording type, default is twitch <youtube, vod, repair>\n'
    usage += '-u, --url     youtube url\n'
    usage += '-v, --vod     twitch vod id\n'
    usage += '-q, --quality recording quality, default is best\n'
    usage += '-p, --path    recording path\n'
    usage += '-c, --command streamlink command\n'
    usage += '\n'
    usage += 'Examples:\n'
    usage += 'Recording twitch stream:\nrecorder.py -n username -t twitch -q best -c --twitch-disable-hosting\n'
    usage += 'Recording twitch vod:\nrecorder.py -n username -t vod -v 13245678\n'
    usage += 'Recording youtube stream: recorder.py -n name -t youtube -u url -q 720p -p /recording\n'
    usage += 'Repairing files in the recorded directory:\nrecorder.py -n name -t repair'

    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'hn:u:t:v:q:p:c:', ['name=',
                                                                             'url=',
                                                                             'type=',
                                                                             'vod=',
                                                                             'quality=',
                                                                             'path=',
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
        elif opt in ('-p', '--path'):
            recorder.root_path = arg
        elif opt in ('-c', '--command'):
            recorder.command = arg

    recorder.run()


if __name__ == "__main__":
    main(sys.argv[1:])
