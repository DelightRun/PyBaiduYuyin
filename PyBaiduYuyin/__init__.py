#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Library for performing speech recognition with Baidu Speech Recognition API."""

__author__ = "Changxu Wang"
__version__ = "0.1.1"
__license__ = "BSD"

import io, os, subprocess, wave
import math, audioop, collections
import json

try: # try to use python2 module
    from urllib import urlencode
    from urllib2 import Request, urlopen, URLError
except ImportError: # otherwise, use python3 module
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    from urllib.parse import urlencode

DEFAULT_APP_KEY = "BElGG5nsGL8oevAa3gMzMk4Y"
DEFAULT_SECRET_KEY = "uVla1FdpQ2HgmojeY9e6pobrS3lRGaeY"

def GetToken(app_key, secret_key):
    data = {'grant_type': 'client_credentials', 'client_id': app_key, 'client_secret': secret_key}
    response = urlopen("https://openapi.baidu.com/oauth/2.0/token", data=urlencode(data))
    response_text = response.read().decode("utf-8")
    json_result = json.loads(response_text)
    return json_result['access_token']

#wip: filter out clicks and other too short parts

class AudioSource(object):
    def __init__(self):
        raise NotImplementedError("this is an abstract class")

    def __enter__(self):
        raise NotImplementedError("this is an abstract class")

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError("this is an abstract class")

try:
    import pyaudio
    class Microphone(AudioSource):
        """
        This is available if PyAudio is available, and is undefined otherwise.

        Creates a new ``Microphone`` instance, which represents a physical microphone on the computer. Subclass of ``AudioSource``.

        If ``device_index`` is unspecified or ``None``, the default microphone is used as the audio source. Otherwise, ``device_index`` should be the index of the device to use for audio input.
        """
        def __init__(self, device_index = None):
            assert device_index is None or isinstance(device_index, int), "Device index must be None or an integer"
            if device_index is not None: # ensure device index is in range
                audio = pyaudio.PyAudio(); count = audio.get_device_count(); audio.terminate() # obtain device count
                assert 0 <= device_index < count, "Device index out of range"
            self.device_index = device_index
            self.format = pyaudio.paInt16 # 16-bit int sampling
            self.SAMPLE_WIDTH = pyaudio.get_sample_size(self.format)
            self.RATE = 16000 # sampling rate in Hertz
            self.CHANNELS = 1 # mono audio
            self.CHUNK = 1024 # number of frames stored in each buffer

            self.audio = None
            self.stream = None

        def __enter__(self):
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                input_device_index = self.device_index,
                format = self.format, rate = self.RATE, channels = self.CHANNELS, frames_per_buffer = self.CHUNK,
                input = True, # stream is an input stream
            )
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.audio.terminate()
except ImportError:
    pass

class WavFile(AudioSource):
    """
    Creates a new ``WavFile`` instance, which represents a WAV audio file. Subclass of ``AudioSource``.

    If ``filename_or_fileobject`` is a string, then it is interpreted as a path to a WAV audio file on the filesystem. Otherwise, ``filename_or_fileobject`` should be a file-like object such as ``io.BytesIO`` or similar. In either case, the specified file is used as the audio source.
    """

    def __init__(self, filename_or_fileobject):
        if isinstance(filename_or_fileobject, str):
            self.filename = filename_or_fileobject
        else:
            assert filename_or_fileobject.read, "Given WAV file must be a filename string or a file object"
            self.filename = None
            self.wav_file = filename_or_fileobject
        self.stream = None

    def __enter__(self):
        if self.filename: self.wav_file = open(self.filename, "rb")
        self.wav_reader = wave.open(self.wav_file, "rb")
        self.SAMPLE_WIDTH = self.wav_reader.getsampwidth()
        self.RATE = self.wav_reader.getframerate()
        self.CHANNELS = self.wav_reader.getnchannels()
        assert self.CHANNELS == 1 # audio must be mono
        self.CHUNK = 4096
        self.stream = WavFile.WavStream(self.wav_reader)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.filename: self.wav_file.close()
        self.stream = None

    class WavStream(object):
        def __init__(self, wav_reader):
            self.wav_reader = wav_reader

        def read(self, size = -1):
            if size == -1:
                return self.wav_reader.readframes(self.wav_reader.getnframes())
            return self.wav_reader.readframes(size)

class AudioData(object):
    def __init__(self, rate, data):
        self.rate = rate
        self.data = data

class TTS(object):
    def __init__(self, language = "zh", app_key = DEFAULT_APP_KEY, secret_key = DEFAULT_SECRET_KEY):
        """
        Create a new ``TTS`` instance, which represents a collection of text-to-speech functionality

        @:param language: language, ``en`` for English, ``zh`` for Chinese
        @:param app_key: Baidu App Key, the default value should only be used for test
        @:param secret_key: Baidu Secret Key, the default value should only be used for test
        """
        assert isinstance(language, str), "Language code must be a string"
        assert isinstance(app_key, str), "Key must be a string"
        assert isinstance(secret_key, str), "Key must be a string"
        self.app_key = app_key
        self.secret_key = secret_key
        self.language = language

        self.energy_threshold = 300 # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 0.8 # seconds of quiet time before a phrase is considered complete
        self.quiet_duration = 0.5 # amount of quiet time to keep on both sides of the recording

        self.token = GetToken(self.app_key, self.secret_key)

    def say(self, text, spd=5, pit=5, vol=5, per=0):
        """
        Perform TTS on the input text ``text``.

        @:param text: text to translation
        @:param spd: [optional] speed, range from 0 to 9
        @:param pit: [optional] pitch, 0-9
        @:param vol: [optional] volumn, 0-9
        @:param person: [optional] 0 for female, 1 for male
        """
        if len(text) > 1024:
            raise KeyError("Text length must less than 1024 bytes")
        url = "http://tsn.baidu.com/text2audio"

        data = {
                "tex": text,
                "lan": self.language,
                "tok": self.token,
                "ctp": 1,
                "cuid": '93489083242',
                "spd": spd,
                "pit": pit,
                "vol": vol,
                "per": per,
                }
        self.request = Request(url, data = urlencode(data))

        # check error
        try:
            response = urlopen(self.request)
        except URLError:
            raise IndexError("No internet connection available to transfer audio data")
        except:
            raise KeyError("Server wouldn't respond (invalid key or quota has been maxed out)")

        content_type = response.info().getheader('Content-Type')
        if content_type.startswith('application/json'):
            response_text = response.read().decode("utf-8")
            json_result = json.loads(response_text)
            raise LookupError("%d - %s" % (json_result['err_no'], json_result['err_msg']))
        elif content_type.startswith('audio/mp3'):
            self.play_mp3(response.read())

    def play_mp3(self, mp3_data):
        import platform, os, stat
        # determine which player executable to use
        system = platform.system()
        path = os.path.dirname(os.path.abspath(__file__)) # directory of the current module file, where all the FLAC bundled binaries are stored
        player = shutil_which("mpg123") # check for installed version first
        if player is None: # flac utility is not installed
            if system == "Windows" and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]: # Windows NT, use the bundled FLAC conversion utility
                player = os.path.join(path, "player", "mpg123-win32.exe")
            elif system == "Linux" and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]:
                player = os.path.join(path, "player", "mpg123-linux")
            elif system == 'Darwin' and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]:
                player = os.path.join(path, "player", "mpg123-mac")
            else:
                raise OSError("MP3 player utility not available - consider installing the MPG123 command line application using `brew install mpg123` or your operating system's equivalent")

        try:
            stat_info = os.stat(player)
            os.chmod(player, stat_info.st_mode | stat.S_IEXEC)
        except OSError:
            pass

        process = subprocess.Popen("\"%s\" -q -" % player, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        play_info, stderr = process.communicate(mp3_data)
        return play_info


class Recognizer(AudioSource):
    def __init__(self, language = "zh", app_key = DEFAULT_APP_KEY, secret_key = DEFAULT_SECRET_KEY):
        """
        Creates a new ``Recognizer`` instance, which represents a collection of speech recognition functionality.

        @:param language: language, ``en`` for English, ``zh`` for Chinese
        @:param app_key: Baidu App Key, the default value should only be used while testing
        @:param secret_key: Baidu Secret Key, the default value should only be used while testing
        """
        assert isinstance(language, str), "Language code must be a string"
        assert isinstance(app_key, str), "Key must be a string"
        assert isinstance(secret_key, str), "Key must be a string"
        self.app_id = app_key
        self.secret_id = secret_key
        self.language = language

        self.energy_threshold = 300 # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 0.8 # seconds of quiet time before a phrase is considered complete
        self.quiet_duration = 0.5 # amount of quiet time to keep on both sides of the recording

        self.token = self.get_token()

    def get_token(self):
        data = {'grant_type': 'client_credentials', 'client_id': self.app_id, 'client_secret': self.secret_id}
        response = urlopen("https://openapi.baidu.com/oauth/2.0/token", data=urlencode(data))
        response_text = response.read().decode("utf-8")
        json_result = json.loads(response_text)
        return json_result['access_token']

    def samples_to_flac(self, source, frame_data):
        assert isinstance(source, AudioSource), "Source must be an audio source"
        import platform, os, stat
        with io.BytesIO() as wav_file:
            wav_writer = wave.open(wav_file, "wb")
            try: # note that we can't use context manager due to Python 2 not supporting it
                wav_writer.setsampwidth(source.SAMPLE_WIDTH)
                wav_writer.setnchannels(source.CHANNELS)
                wav_writer.setframerate(source.RATE)
                wav_writer.writeframes(frame_data)
            finally:  # make sure resources are cleaned up
                wav_writer.close()
            wav_data = wav_file.getvalue()

        # determine which converter executable to use
        system = platform.system()
        path = os.path.dirname(os.path.abspath(__file__)) # directory of the current module file, where all the FLAC bundled binaries are stored
        flac_converter = shutil_which("flac") # check for installed version first
        if flac_converter is None: # flac utility is not installed
            if system == "Windows" and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]: # Windows NT, use the bundled FLAC conversion utility
                flac_converter = os.path.join(path, "flac", "flac-win32.exe")
            elif system == "Linux" and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]:
                flac_converter = os.path.join(path, "flac", "flac-linux")
            elif system == 'Darwin' and platform.machine() in ["i386", "x86", "x86_64", "AMD64"]:
                flac_converter = os.path.join(path, "flac", "flac-mac")
            else:
                raise OSError("FLAC conversion utility not available - consider installing the FLAC command line application using `brew install flac` or your operating system's equivalent")

        # mark covnerter as executable
        try:
            stat_info = os.stat(flac_converter)
            os.chmod(flac_converter, stat_info.st_mode | stat.S_IEXEC)
        except OSError: pass

        process = subprocess.Popen("\"%s\" --stdout --totally-silent --best -" % flac_converter, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        flac_data, stderr = process.communicate(wav_data)
        return flac_data

    def record(self, source, duration = None):
        """
        Records up to ``duration`` seconds of audio from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

        If ``duration`` is not specified, then it will record until there is no more audio input.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"

        frames = io.BytesIO()
        seconds_per_buffer = (source.CHUNK + 0.0) / source.RATE
        elapsed_time = 0
        while True: # loop for the total number of chunks needed
            elapsed_time += seconds_per_buffer
            if duration and elapsed_time > duration: break

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break
            frames.write(buffer)

        frame_data = frames.getvalue()
        frames.close()
        return AudioData(source.RATE, self.samples_to_flac(source, frame_data))

    def adjust_for_ambient_noise(self, source, duration = 1):
        """
        Adjusts the energy threshold dynamically using audio from ``source`` (an ``AudioSource`` instance) to account for ambient noise.

        Intended to calibrate the energy threshold with the ambient energy level. Should be used on periods of audio without speech - will stop early if any speech is detected.

        The ``duration`` parameter is the maximum number of seconds that it will dynamically adjust the threshold for before returning. This value should be at least 0.5 in order to get a representative sample of the ambient noise.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"

        seconds_per_buffer = (source.CHUNK + 0.0) / source.RATE
        elapsed_time = 0

        # adjust energy threshold until a phrase starts
        while True:
            elapsed_time += seconds_per_buffer
            if elapsed_time > duration: break
            buffer = source.stream.read(source.CHUNK)

            # check if the audio input has stopped being quiet
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH) # energy of the audio signal
            if energy > self.energy_threshold: break

            # dynamically adjust the energy threshold using assymmetric weighted average
            damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer # account for different chunk sizes and rates
            target_energy = energy * self.dynamic_energy_ratio
            self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

    def listen(self, source, timeout = None):
        """
        Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

        This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of silence or there is no more audio input. The ending silence is not included.

        The ``timeout`` parameter is the maximum number of seconds that it will wait for a phrase to start before giving up and throwing a ``TimeoutException`` exception. If ``None``, it will wait indefinitely.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"

        # record audio data as raw samples
        frames = collections.deque()
        assert self.pause_threshold >= self.quiet_duration >= 0
        seconds_per_buffer = (source.CHUNK + 0.0) / source.RATE
        pause_buffer_count = int(math.ceil(self.pause_threshold / seconds_per_buffer)) # number of buffers of quiet audio before the phrase is complete
        quiet_buffer_count = int(math.ceil(self.quiet_duration / seconds_per_buffer)) # maximum number of buffers of quiet audio to retain before and after
        elapsed_time = 0

        # store audio input until the phrase starts
        while True:
            elapsed_time += seconds_per_buffer
            if timeout and elapsed_time > timeout: # handle timeout if specified
                raise TimeoutError("listening timed out")

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break # reached end of the stream
            frames.append(buffer)

            # check if the audio input has stopped being quiet
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH) # energy of the audio signal
            if energy > self.energy_threshold: break

            # dynamically adjust the energy threshold using assymmetric weighted average
            if self.dynamic_energy_threshold:
                damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer # account for different chunk sizes and rates
                target_energy = energy * self.dynamic_energy_ratio
                self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

            if len(frames) > quiet_buffer_count: # ensure we only keep the needed amount of quiet buffers
                frames.popleft()

        # read audio input until the phrase ends
        pause_count = 0
        while True:
            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break # reached end of the stream
            frames.append(buffer)

            # check if the audio input has gone quiet for longer than the pause threshold
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH) # energy of the audio signal
            if energy > self.energy_threshold:
                pause_count = 0
            else:
                pause_count += 1
            if pause_count > pause_buffer_count: # end of the phrase
                break

         # obtain frame data
        for i in range(quiet_buffer_count, pause_count): frames.pop() # remove extra quiet frames at the end
        frame_data = b"".join(list(frames))

        return AudioData(source.RATE, self.samples_to_flac(source, frame_data))

    def recognize(self, audio_data):
        """
        Performs speech recognition, using the Google Speech Recognition API, on ``audio_data`` (an ``AudioData`` instance).

        Return the most likely text
        """
        assert isinstance(audio_data, AudioData), "Data must be audio data"

        import base64
        url = "http://vop.baidu.com/server_api"

        data = {
                "format": "x-flac",
                "lan": self.language,
                "token": self.token,
                "len": len(audio_data.data),
                "rate": audio_data.rate,
                "speech": base64.b64encode(audio_data.data),
                "cuid": '93489083242',
                "channel": 1,
                }
        self.request = Request(url, data = json.dumps(data), headers = {"Content-Type": "application/json"})

        # check for invalid key response from the server
        try:
            response = urlopen(self.request)
        except URLError:
            raise IndexError("No internet connection available to transfer audio data")
        except:
            raise KeyError("Server wouldn't respond (invalid key or quota has been maxed out)")

        response_text = response.read().decode("utf-8")
        json_result = json.loads(response_text)
        if int(json_result['err_no']) != 0:
            raise LookupError(json_result['err_msg'])
        else:
            return json_result['result'][0]

    def listen_in_background(self, source, callback):
        """
        Spawns a thread to repeatedly record phrases from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance and call ``callback`` with that ``AudioData`` instance as soon as each phrase are detected.

        Returns the thread (a ``threading.Thread`` instance) immediately, while the background thread continues to run in parallel.

        Phrase recognition uses the exact same mechanism as ``recognizer_instance.listen(source)``.

        The ``callback`` parameter is a function that should accept two parameters - the ``recognizer_instance``, and an ``AudioData`` instance representing the captured audio. Note that this function will be called from a non-main thread.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        import threading
        def threaded_listen():
            while True:
                with source as s: audio = self.listen(s)
                callback(self, audio)
        listener_thread = threading.Thread(target=threaded_listen)
        listener_thread.start()
        return listener_thread

def shutil_which(pgm):
    """
    python2 backport of python3's shutil.which()
    """
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p

if __name__ == "__main__":
    t = TTS()
    r = Recognizer()
    m = Microphone()

    t.say("你好，这里是百度语音识别模块测试")

    while True:
        print("Say something!")
        with m as source:
            audio = r.listen(source)
        print("Got it! Now to recognize it...")
        try:
            text = r.recognize(audio)
            print 'You said ' + text
        except LookupError:
            print("Oops! Didn't catch that")
