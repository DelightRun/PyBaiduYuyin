PyBaiduYuyin
============

This project is a wrap for [Baidu Yuyin(voice) API](http://yuyin.baidu.com/)

This project is modified from [SpeechRecognition](https://github.com/Uberi/speech_recognition)

cite:

    Zhang, A. (2015). Speech Recognition (Version 1.4) [Software]. Available from https://github.com/Uberi/speech_recognition#readme.
    
    Zhang, Anthony. 2015. *Speech Recognition* (version 1.4).
    
Requirement
===========

+ PyAudio

Usage
=====

### TTS

~~~{python}
import PyBaiduYuyin as pby
tts = pby.TTS(app_key=YOUR_APP_KEY, secret_key=YOUR_SECRET_KEY)
tts.say("你好")
~~~

### Recognition

The usage of Recognition module is same as [SpeechRecognition](https://github.com/Uberi/speech_recognition), except use

`Baidu App Key` and `Baidu Secret Key` instead of `Google App Key`.

Please see [SpeechRecognition's README](https://github.com/Uberi/speech_recognition/blob/master/README.rst) for details.

LICENSE
=======

please see `LICENSE.txt` in this project.