# -*- coding: UTF-8 -*-

import os
import base64
from config import n, src_file_type


def wav2pcm(*args):
    files = args if args else range(1, n)
    for i in files:
        os.system("ffmpeg -y -i %s.%s -f s16be -ac 1 -ar 16000 -acodec pcm_s16le %s.pcm" % (i, src_file_type, i))


def pcm2base64(*args):
    files = args if args else range(1, n)
    for i in files:
        with open("%s.pcm" % i, "rb") as pf:
            pcm = pf.read()
            base64_str = base64.b64encode(pcm)
            with open("%s.b64" % i, "wb") as bf:
                bf.write(base64_str)


