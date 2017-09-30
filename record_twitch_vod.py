import requests
import os
import sys
import subprocess
import getopt


class Recorder:
    def __init__(self):
        self.client_id = "jzkbprff40iqj646a697cyrvl0zt2m6"  # don't change this
        self.root_path = os.path.abspath('')
        self.quality = "best"

    def get_vod(self):
        url = 'https://api.twitch.tv/kraken/videos/' + self.vod
        info = None
        r = requests.get(url, headers={"Client-ID": self.client_id}, timeout=15)
        r.raise_for_status()
        info = r.json()
        filename = info['channel']['name'] + "_" + info['published_at'] + ".mp4"
        filename = "".join(x for x in filename if x.isalnum() or x in ["-", "_", "."])

        self.recorded_path = os.path.join(self.root_path, "recorded", info['channel']['name'])
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        recorded_filename = os.path.join(self.recorded_path, filename)

        self.processed_path = os.path.join(self.root_path, "processed", info['channel']['name'])
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)
        processed_filename = os.path.join(self.processed_path, filename)

        print("Vod recording in session.")
        subprocess.call(['streamlink', 'twitch.tv/videos/' + self.vod, self.quality, '-o', recorded_filename])
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


def main(argv):
    recorder = Recorder()
    usage_message = 'twitch_vod.py -v <vod>'

    try:
        opts, args = getopt.getopt(argv, "hv:", ["vod="])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-v", "--vod"):
            recorder.vod = arg

    recorder.get_vod()


if __name__ == "__main__":
    main(sys.argv[1:])
