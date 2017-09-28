import requests
import os
import time
import subprocess
import datetime
import getopt
import sys


class Recorder:
    def __init__(self):
        self.client_id = "jzkbprff40iqj646a697cyrvl0zt2m6"  # don't change this
        self.refresh = 15.0
        self.quality = "best"
        self.username = ""
        self.root_path = os.path.abspath('')

    def run(self):
        self.recorded_path = os.path.join(self.root_path, "recorded", self.username)
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        self.processed_path = os.path.join(self.root_path, "processed", self.username)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        if(self.refresh < 15):
            print("Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print("System set check interval to 15 seconds.")

        try:
            video_list = [f for f in os.listdir(self.recorded_path) if os.path.isfile(os.path.join(self.recorded_path, f))]
            if(len(video_list) > 0):
                print('Fixing previously recorded files.')
            for f in video_list:
                recorded_filename = os.path.join(self.recorded_path, f)
                processed_filename = os.path.join(self.processed_path, f)
                print('Fixing ' + recorded_filename + '.')
                try:
                    subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', processed_filename])
                    os.remove(recorded_filename)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

        print("Checking for", self.username, "every", self.refresh, "seconds. Record with", self.quality, "quality.")
        self.loopcheck()

    def check_user(self):
        url = 'https://api.twitch.tv/kraken/streams/' + self.username
        info = None
        status = 3  # 3: error
        try:
            r = requests.get(url, headers={"Client-ID": self.client_id}, timeout=15)
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
        return status, info

    def loopcheck(self):
        while True:
            status, info = self.check_user()
            if status == 2:
                print("Username not found. Invalid username or typo.")
                time.sleep(self.refresh)
            elif status == 3:
                print(datetime.datetime.now().strftime("%Hh%Mm%Ss"), " ", "unexpected error. will try again in 5 minutes.")
                time.sleep(300)
            elif status == 4:
                print(self.username, "currently vodcasting, checking again in", self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 1:
                print(self.username, "currently offline, checking again in", self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 0:
                print(self.username, "online. Stream recording in session.")

            filename = self.username + "_" + datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss") + ".mp4"
            filename = "".join(x for x in filename if x.isalnum() or x in ["-", "_", "."])

            recorded_filename = os.path.join(self.recorded_path, filename)
            processed_filename = os.path.join(self.processed_path, filename)

            subprocess.call(['streamlink', 'twitch.tv/' + self.username, self.quality, "-o", recorded_filename])

            print("Recording stream is done.")
            if(os.path.exists(recorded_filename) is True):
                print("Fixing video file.")
                try:
                    subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', processed_filename])
                    os.remove(recorded_filename)
                except Exception as e:
                    print(e)
            else:
                print("Skip fixing. File not found.")

            time.sleep(self.refresh)


def main(argv):
    recorder = Recorder()
    usage_message = 'twitch_stream.py -u <username>'

    try:
        opts, args = getopt.getopt(argv, "hu:", ["user="])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-u", "--user"):
            recorder.username = arg

    recorder.run()


if __name__ == "__main__":
    main(sys.argv[1:])
