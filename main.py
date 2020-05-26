import base64
import os
import sys
import requests
import json
import time

n = 0
src_file_type = ""
if getattr(sys, 'frozen', False):  # 是否Bundle Resource
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")
ffmpeg_exec = os.path.join(base_path, "ffmpeg.exe")

codes = {
    40007: "声音太小",
    40008: "出现了一些小问题",
    40009: "多读了",
}
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

headers = {
    "user-agent": "Mi 10; MIAI/5.8.6-202004101658-28 Build/305008006 Channel/MIUI20.3.28 Device/umi OS/10 SDK/29 "
                  "Flavors/upgrade28",
}

new_data = {
    "train_data_url": [
    ],
    "device_id": "f78269897b6cc7b856541f61ca2f7yhg5",
    "audio_format": {
        "codec": "pcm",
        "rate": 16000,
        "bits": 16,
        "channel": 1,
        "lang": "zh-CN"
    },
    "request_id": "45632561tyuiop05c34ef0bbcc888"
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
            "%s -y -i %s.%s -f s16be -ac 1 -ar 16000 -acodec pcm_s16le pcm/%s.pcm" % (ffmpeg_exec, i, src_file_type, i))


def pcm2base64(args):
    files = args if args else range(1, n)
    for i in files:
        with open("pcm/%s.pcm" % i, "rb") as pf:
            pcm = pf.read()
            base64_str = base64.b64encode(pcm)
            with open("b64/%s.b64" % i, "wb") as bf:
                bf.write(base64_str)


def asr_audio(args):
    files = args if args else range(1, n)
    result_html = open("result.html", "w")
    error_nos = []
    for i in files:
        with open("b64/%s.b64" % i, "r") as f:
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
                    error_nos.append(i)
                    result_html.write(result["text"]
                                      .replace("<html><body>", "<div>{}. ".format(i))
                                      .replace("</body></html>", " <span style=\"color:red\">({})</span></div>"
                                               .format(codes.get(result["sub_code"], result["sub_code"]))))
            else:
                print("第 %s 条校验失败！可能是Authorization不正确。http_code: %s resp: %s" % (i, resp.status_code, resp.text))
                error_nos.append(i)
    rf = open("result.json", "w")
    rf.write(json.dumps({"error_nos": error_nos}))
    rf.close()
    result_html.close()


def process_record():
    print("开始处理声音文件...")
    if not os.path.exists("pcm") and not os.path.exists("b64"):
        os.mkdir("pcm")
        os.mkdir("b64")
    try:
        rf = open("result.json", "r")
        rf_str = rf.readline().strip()
        args = None
        if rf_str:
            args = json.loads(rf_str).get("error_nos")
        rf.close()
        if args:
            print("仅处理第 {} 条".format(args))
    except FileNotFoundError:
        args = None
    if src_file_type == "pcm":
        os.system("copy *.pcm pcm")
    else:
        wav2pcm(args)
    pcm2base64(args)

    print("处理完成。")


def verify_record():
    print("开始检验声音...")
    try:
        rf = open("result.json", "r")
        rf_str = rf.readline().strip()
        args = None
        if rf_str:
            args = json.loads(rf_str).get("error_nos")
        if args:
            print("仅检验第 {} 条".format(args))
    except FileNotFoundError:
        args = None
    asr_audio(args)


def upload_record():
    for i in range(1, n):
        with open("b64/%s.b64" % i, "r") as f:
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


def post_record():
    new_data["model_name"] = input("请输入音色名称：")
    while True:
        inp = input("请选择性别(男生：1，女生：2)：")
        if inp != '1' and inp != '2':
            print("输入错误，请重新输入")
            continue
        new_data["user_gender"] = "male" if inp == '1' else "female"
        break
    resp = requests.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/train",
                         json=new_data,
                         headers=headers)
    if resp.status_code == 200:
        print("音色提交结果：")
        print(resp.text)
    else:
        print("音色提交失败，code: %s, resp: %s" % (resp.status_code, resp.text))


def getAuthorization():
    try:
        af = open("Authorization.txt", 'r')
        Authorization = af.readline().strip()
        af.close()
        headers["Authorization"] = Authorization
        resp = requests.get("https://speech.ai.xiaomi.com/speech/v1.0/ptts/list",
                            headers=headers)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["code"] != 200:
                print("上次的Authorization已经失效")
                raise FileNotFoundError
            else:
                inp = input("是否继续使用上次的Authorization？(输入 no 将重新输入Authorization，按回车继续使用上次的Authorization)")
                if inp and inp == "no":
                    raise FileNotFoundError
        else:
            print("上次的Authorization已经失效")
            raise FileNotFoundError
    except FileNotFoundError:
        af = open("Authorization.txt", 'w')
        while True:
            Authorization = input("请输入Authorization(抓包获取，详见教程)：")
            headers["Authorization"] = Authorization
            resp = requests.get("https://speech.ai.xiaomi.com/speech/v1.0/ptts/list",
                                headers=headers)
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json["code"] != 200:
                    print("Authorization无效，请重新输入")
                    continue
                else:
                    af.write(Authorization)
                    break
            else:
                print("Authorization无效，请重新输入")
                continue


if __name__ == '__main__':
    print("本程序支持常见的声音格式例如，mp3 wav m4a等。")
    print("也可以直接使用pcm文件。")
    print("开始之前，请先完成以下准备工作\n")
    print("1. 将待处理的20/30个声音文件命名为1-20.后缀,\n"
          "   例如，你的原始声音文件为mp3格式，那就将其命名\n"
          "   为1.mp3 2.mp3... 直到20.mp3或者30.mp3\n")
    print("   注意，声音文件个数只支持20个或者30个，不能多不能少\n")
    print("2. 在声音文件所在的目录下新建一个名为 texts.txt 的文件，\n"
          "   将每个声音对应的文字信息写入该文件\n"
          "   (一行一个，注意标点符号全部使用中文标点)\n")
    print("   注意，该文件中的每一行文字，要和每一个\n"
          "   声音文件的内容一一对应，因此，该文件总共有20行或者30行\n")
    input("准备就绪后按任意键继续...")
    while True:
        work_dir = input("请输入工作目录(原始声音文件所在目录的绝对路径，例如：D:\\Data\\lubenwei)：")
        if not work_dir or not os.path.exists(work_dir):
            print("输入的目录不存在！请重新输入。")
            continue
        break
    os.chdir(work_dir)
    src_file_type = input("请输入原始文件格式(mp3/wav/m4a/pcm等)：")
    while True:
        try:
            text = open("texts.txt")
            texts = text.readlines()
            text.close()
            texts = [text.strip() for text in texts]
            break
        except FileNotFoundError:
            input("工作目录下texts.txt不存在，请按要求放入该文件，然后按回车继续")
            continue

    n = len(texts) + 1
    is_error = True
    while is_error:
        is_error = False
        for i in range(1, n):
            with open("{}.{}".format(i, src_file_type), "r") as f:
                if not f:
                    print("声音文件 {}.{} 不存在。".format(i, src_file_type))
                    is_error = True
        if is_error:
            input("存在错误，请处理完按任意键继续...")
    open("result.json", "w").close()
    getAuthorization()
    print("文件准备就绪，开始处理")
    while True:
        process_record()
        verify_record()
        rf = open("result.json", "r")
        args = json.loads(rf.readline().strip()).get("error_nos")
        if not args:
            break
        else:
            print("声音 {} 检验失败，具体错误原因请用浏览器打开工作目录下的result.html文件".format(args))
            print("请重新准备这几个声音文件，然后按回车继续")
            inp = input("你也可以强行提交，但是会导致训练结果很差，如果要强行提交，请输入 force ：")
            if inp == "force":
                break
    print("校验通过，开始上传。")
    upload_record()
    post_record()
    input("执行结束，按任意键关闭窗口。")
