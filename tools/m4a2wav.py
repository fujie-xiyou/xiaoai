import os
import config

"""
如果你的音频文件是m4a可以用这个文件处理
"""

for i in range(1, 21):
    os.system("ffmpeg -i %s.m4a -ac 1 -ar 16000 -acodec pcm_s16le -f wav %s.wav" % (i, i))
