import sys
from tools.record_converter import wav2pcm
from tools.record_converter import pcm2base64

if __name__ == '__main__':
    args = []
    for i in range(1, len(sys.argv)):
        args.append(int(sys.argv[i]))
    wav2pcm(*args)
    pcm2base64(*args)
