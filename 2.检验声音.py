import sys
from tools.req import asr_audio

if __name__ == '__main__':
    args = []
    for i in range(1, len(sys.argv)):
        args.append(int(sys.argv[i]))
    asr_audio(*args)

