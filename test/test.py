import requests
import time
import os

os.chdir("/Users/fujie/Downloads/lu")
headers = {
    "user-agent": "Mi 10; MIAI/5.8.6-202004101658-28 Build/305008006 Channel/MIUI20.3.28 Device/umi OS/10 SDK/29 "
                  "Flavors/upgrade28",
    "Authorization": "AO-TOKEN-V1 dev_app_id:2882303761517844702,scope_data:eyJkIjoiZWM1YmUzNTAwNzhjZGRkYyJ9,"
                     "access_token:V3_piKMZzH_xkNddFTAT02iT5DjhQdOI3hG6AkYosJYtGvS0PDJZWzPuQkHagkTrOBVqDyWvUe4x0mi80oiSMoi9WJwz9hhk_J8EJAIk4brN80NIkFtpafXgHXJO0Ss9WcT"
}

with open("b64/%s.b64" % 1, "r") as f:
    audio_data = f.read()
    asr_data = {
        "httpAsrRequest": {
            "asr_format": {
                "codec": "pcm",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
                "lang": "zh-CN"
            },
            "asr_audio": '音频内容',
            "request_id": "到时候给个时间戳"
        },
        "originText": "首先，我今天要讲两个东西，最近针对于我卢本伟开外挂的风波。"
    }
    asr_data["httpAsrRequest"]["asr_audio"] = audio_data
    asr_data["httpAsrRequest"]["request_id"] = str(int(time.time()))
    resp = requests.post(url="https://speech.ai.xiaomi.com/speech/v1.0/asr/ptts/detect",
                         json=asr_data,
                         headers=headers)
    print(resp.text)
