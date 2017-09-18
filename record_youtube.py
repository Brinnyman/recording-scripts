import os
import time
import subprocess
import datetime


class Recorder:
    def __init__(self):
        self.refresh = 15.0
        self.username = ''
        self.url = ''
        self.quality = 'best'
        self.root_path = os.path.abspath('')
        self.recorded_path = os.path.join(self.root_path, "recorded", self.username)
        self.processed_path = os.path.join(self.root_path, "processed", self.username)

    def run(self):
        pass
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        if(self.refresh < 15):
            print("Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print("System set check interval to 15 seconds.")

        print("Checking for", self.username, "every", self.refresh, "seconds. Record with", self.quality, "quality.")
        self.loopcheck()

    def loopcheck(self):
        while True:
            filename = "yt" + "-" + datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss") + ".mp4"
            filename = "".join(x for x in filename if x.isalnum() or x in ["-", "_", "."])

            recorded_filename = os.path.join(self.recorded_path, filename)
            processed_filename = os.path.join(self.processed_path, filename)

            subprocess.call(['streamlink', self.url, self.quality, "-o", recorded_filename])

            if(os.path.exists(recorded_filename) is True):
                print("Recording stream is done. Fixing video file.")
                try:
                    subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', processed_filename])
                    os.remove(recorded_filename)
                except Exception as e:
                    print(e)

            time.sleep(self.refresh)


if __name__ == "__main__":
    recorder = Recorder()
    recorder.run()
