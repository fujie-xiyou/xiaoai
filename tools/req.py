# -*- coding: UTF-8 -*-
import requests
import json
import time
from config import Authorization, name, sex, texts, n
from tools.error_code import codes

data = {
    "audio_data": "",
    "audio_format": {
        "codec": "pcm",
        "rate": 16000,
        "bits": 16,
        "channel": 1,
        "lang": "zh-CN"
    },
    "request_id": ""
}

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
    "originText": "文本"
}
new_data = {
    "train_data_url": [
    ],
    "device_id": "d7a269897b6cc7b71365f61ca2f7b2ed",
    "model_name": name,
    "audio_format": {
        "codec": "pcm",
        "rate": 16000,
        "bits": 16,
        "channel": 1,
        "lang": "zh-CN"
    },
    "user_gender": sex,
    "request_id": "101bf0a11bd94eea905c34ef0bbcc888"
}

headers = {
    "user-agent": "Mi 10; MIAI/5.8.6-202004101658-28 Build/305008006 Channel/MIUI20.3.28 Device/umi OS/10 SDK/29 Flavors/upgrade28",
    "Authorization": Authorization,
}


def asr_audio(*args):
    files = args if args else range(1, n)
    result_html = open("result.html", "w")

    for i in files:
        with open("%s.b64" % i, "r") as f:
            audio_data = f.read()
            asr_data["originText"] = texts[i - 1]
            asr_data["httpAsrRequest"]["asr_audio"] = audio_data
            asr_data["httpAsrRequest"]["request_id"] = str(int(time.time()))
            resp = requests.post(url="https://speech.ai.xiaomi.com/speech/v1.0/asr/ptts/detect",
                                 json=asr_data,
                                 headers=headers)
            if resp.status_code == 200:
                content = json.loads(resp.text)
                if content["code"] == 200:
                    print("第 %s 条校验成功" % i)
                else:
                    result = resp.json()
                    print("第 %s 条校验失败！原因：%s" % (i, codes.get(result["sub_code"], result["sub_code"])))
                    result_html.write(result["text"]
                                      .replace("<html><body>", "<div>{}. ".format(i))
                                      .replace("</body></html>", " <span style=\"color:red\">({})</span></div>"
                                               .format(codes.get(result["sub_code"], result["sub_code"]))))
            else:
                print("第 %s 条校验失败！http_code: %s resp: %s" % (i, resp.status_code, resp.text))
    result_html.close()


def post_record():
    for i in range(1, n):
        with open("%s.b64" % i, "r") as f:
            audio_data = f.read()
            data["audio_data"] = audio_data
            data["request_id"] = "fujie%s%s" % (i, str(int(time.time())))
            resp = requests.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/upload",
                                 json=data,
                                 headers=headers)
            if resp.status_code == 200:
                print("第 %s 条上传成功" % i)
                item = {"url": json.loads(resp.text)["audio_file"], "id": str(i), "text": texts[i - 1]}
                new_data["train_data_url"].append(item)
            else:
                print("第 %s 条上传失败，code: %s, resp: %s" % (i, resp.status_code, resp.text))

    resp = requests.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/train",
                         json=new_data,
                         headers=headers)
    if resp.status_code == 200:
        print("音色提交结果：")
        print(resp.text)
    else:
        print("音色提交失败，code: %s, resp: %s" % (resp.status_code, resp.text))
