import base64
import json
import os
import random
import string
import sys
import requests
import platform
import logging
import aiohttp
import asyncio

from main import cp_exec, ffmpeg_exec, config_path

n = 0
src_file_type = ''
texts = []

raw_model_path = "/Users/fujie/Desktop/models"

codes = {
    40006: "音量太大",
    40007: "音量太小",
    40008: "出现了一些小问题",
    40009: "多读了",
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

headers = {
    "user-agent": "Mi 10; MIAI/5.8.6-202004101658-28 Build/305008006 Channel/MIUI20.3.28 Device/umi OS/10 SDK/29 "
                  "Flavors/upgrade28",
}


def wav2pcm(args):
    """
    名字虽然叫wav2pcm 但是其实可以将各种声音格式转为pcm
    :param args:
    :return:
    """
    files = args if args else range(1, n)
    for i in files:
        os.system(
            "%s -y -i %s.%s -f s16be -ac 1 -ar 16000 -acodec pcm_s16le .pcm/%s.pcm" % (ffmpeg_exec, i, src_file_type, i))


def pcm2base64(args):
    files = args if args else range(1, n)
    for i in files:
        with open(".pcm/%s.pcm" % i, "rb") as pf:
            pcm = pf.read()
            base64_str = base64.b64encode(pcm)
            with open(".b64/%s.b64" % i, "wb") as bf:
                bf.write(base64_str)


def process_record():
    print("开始处理声音文件...")
    if not os.path.exists(".pcm"):
        os.mkdir(".pcm")
    if not os.path.exists(".b64"):
        os.mkdir(".b64")

    if src_file_type == "pcm":
        os.system("{} *.pcm .pcm".format(cp_exec))
    else:
        wav2pcm(None)
    pcm2base64(None)

    print("处理完成。")


async def _upload_record():
    upload_data = {
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
    post_data = {
        "train_data_url": [
        ],
        "device_id": ''.join(random.sample(string.ascii_letters + string.digits, 22)),
        "audio_format": {
            "codec": "pcm",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
            "lang": "zh-CN"
        },
        "request_id": ''.join(random.sample(string.ascii_letters + string.digits, 22))
    }

    for i in range(1, n):
        with open(".b64/%s.b64" % i, "r") as f:
            audio_data = f.read()
            upload_data["audio_data"] = audio_data
            upload_data["request_id"] = ''.join(random.sample(string.ascii_letters + string.digits, 22))
            async with aiohttp.ClientSession() as session:
                async with session.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/upload",
                                        json=upload_data,
                                        headers=headers,
                                        timeout=5000) as resp:
                    if resp.status == 200:
                        resp_json = await resp.json(content_type=None)
                        if resp_json["code"] == 200:
                            print(f"第{i}条上传成功")
                            item = {"url": resp_json["audio_file"], "id": str(i), "text": texts[i - 1]}
                            post_data["train_data_url"].append(item)
                        else:
                            print(f"第{i}条上传失败，resp: {resp_json}")
                    else:
                        print(f"第{i}条上传失败，status：{resp.status} resp：{await resp.text()}")

    return post_data


def dump_post_data(_raw_model, post_data):
    while True:
        inp = input("请选择性别(男生：1，女生：2)：")
        if inp != '1' and inp != '2':
            print("输入错误，请重新输入")
            continue
        post_data["user_gender"] = "male" if inp == '1' else "female"
        break

    post_data["model_name"] = _raw_model
    _model_path = os.path.join(raw_model_path, ".models")
    if not os.path.exists(_model_path):
        os.mkdir(_model_path)
    f = open(os.path.join(_model_path, f"{_raw_model}.json"), "w")
    content = json.dumps(post_data, ensure_ascii=False, sort_keys=True, indent=True)
    f.write(content)
    f.close()


def get_authorization():
    authorization_path = os.path.join(config_path, "Authorization.txt")
    try:
        af = open(authorization_path, 'r')
        authorization = af.readline().strip()
        af.close()
        headers["Authorization"] = authorization
        while True:
            try:
                resp = requests.get("https://speech.ai.xiaomi.com/speech/v1.0/ptts/list",
                                    headers=headers,
                                    timeout=5)
                break
            except requests.exceptions.RequestException:
                print("请求超时，正在重试...")
                continue
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["code"] != 200:
                print("上次的Authorization已经失效")
                raise FileNotFoundError
        else:
            print("上次的Authorization已经失效")
            raise FileNotFoundError
    except FileNotFoundError:
        af = open(authorization_path, 'w')
        while True:
            authorization = input("请输入Authorization(抓包获取，详见教程)：")
            headers["Authorization"] = authorization
            while True:
                try:
                    resp = requests.get("https://speech.ai.xiaomi.com/speech/v1.0/ptts/list",
                                        headers=headers,
                                        timeout=5)
                    break
                except requests.exceptions.RequestException:
                    print("请求超时，正在重试...")
                    continue
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json["code"] != 200:
                    print("Authorization无效，请重新输入")
                    continue
                else:
                    af.write(authorization)
                    break
            else:
                print("Authorization无效，请重新输入")
                continue


def main(_raw_model):
    work_dir = os.path.join(raw_model_path, _raw_model)
    global texts
    global src_file_type
    global n
    os.chdir(work_dir)
    print(f"开始处理 {_raw_model}")
    files = [file for file in os.listdir(".") if ((not file.startswith(".")) and (file.split(".")[1] in ["mp3", "wav", "m4a", "pcm"]))]
    n = len(files) + 1
    src_file_type = files[0].split(".")[1]
    while True:
        try:
            text = open("texts.txt", encoding="gb18030")
            try:
                texts = text.readlines()
            except UnicodeDecodeError:
                text.close()
                text = open("texts.txt", encoding="utf-8")
                texts = text.readlines()
            text.close()
            texts = [text.strip() for text in texts if text.strip()]
            break
        except FileNotFoundError:
            print("工作目录下texts.txt不存在，将使用白雪公主文本")
            texts_txt_path = os.path.join(raw_model_path, ".texts.txt")
            os.system(f"{cp_exec} {texts_txt_path} texts.txt")

    n = len(texts) + 1
    open("result.json", "w").close()
    get_authorization()
    print("文件准备就绪，开始处理")

    process_record()

    print("开始上传。")
    post_data = asyncio.run(_upload_record())
    print(f"{_raw_model} 上传完成")
    dump_post_data(_raw_model, post_data)
    print(f"{_raw_model} 执行结束")


if __name__ == '__main__':
    try:
        raw_models = [raw_model for raw_model in os.listdir(raw_model_path) if not raw_model.startswith(".")]
        for raw_model in raw_models:
            main(raw_model)
    except Exception as e:
        logging.exception(e)
        input("出现未知错误，请截图反馈，然后按任意键退出...")
