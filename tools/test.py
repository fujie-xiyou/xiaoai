import requests
import time
import os

os.chdir("/Users/fujie/Downloads/lu")
headers = {
    "user-agent": "Mi 10; MIAI/5.8.6-202004101658-28 Build/305008006 Channel/MIUI20.3.28 Device/umi OS/10 SDK/29 "
                  "Flavors/upgrade28",
    "Authorization": "DO-TOKEN-V1 app_id:326813440150602752,scope_data:eyJkIjoiYjljZjkyZWVjMDNlYmJjMyJ9,"
                     "access_token:V3_ic-2pifIZdQ5UM33OpcdPU_rCBCWm89xvYUZZWz3fc81hHSDmJdqEH4Q7omLgOhdyQivfVq0B4"
                     "-ABe20JRup17ag_Ue2oOLHY-YoeHrjmhBF5Tyrmmv_Maiam88HM5IW "
}


a = "DO-TOKEN-V1 app_id:326813440150602752,scope_data:eyJkIjoiYjljZjkyZWVjMDNlYmJjMyJ9," \
    "access_token:V3_zO12DXKMsm7JPEHPcpiGVll62hN5F_4Ja1C4lKxZP3AEC" \
    "-h5p1SFGQHMqGthtA7GVuQB_SzyAbJPmXFrdFmAQJS3hdWNKhmnnn82eOPaPW9I032mvhH" \
    "--_B0zDcOAhmGif97K3aR7ecgYsRE75aYHa8Hxunaw1GeQJipG0DeVQs "
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
