PyBaiduYuyin
============

This project is a wrapper for `Baidu Yuyin(voice)
API <http://yuyin.baidu.com/>`__

This project is modified from
`SpeechRecognition <https://github.com/Uberi/speech_recognition>`__,
which is published under the 3-clause BSD license.

Requirement
===========

-  PyAudio

Install
=======

::

    $ pip install PyBaiduYuyin

Usage
=====

    Note: I'm still working on this part, contributions are welcomed.

TTS (Text-To-Speech)
~~~~~~~~~~~~~~~~~~~~

Details can be found in source code.

Example:

::

    import PyBaiduYuyin as pby
    tts = pby.TTS(app_key=YOUR_APP_KEY, secret_key=YOUR_SECRET_KEY)
    tts.say("你好")

Recognition
~~~~~~~~~~~

The usage of Recognition module is same as
`SpeechRecognition <https://github.com/Uberi/speech_recognition>`__,
except using ``Baidu App Key`` and ``Baidu Secret Key`` instead of
``Google App Key``.

Please see `SpeechRecognition's
README <https://github.com/Uberi/speech_recognition/blob/master/README.rst>`__
for details.

LICENSE
=======

Copyright (c) 2015-2016 `Changxu Wang <changxu.wang>`__

The source code is available online at GitHub.

This program is made available under **MIT License**, see
``LICENSE.txt`` for details.
