import base64
import os
import random
import string
import sys
import requests
import json
import platform
import logging
import websocket
import datetime
import hashlib
import hmac
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

n = 0
src_file_type = ""
run_path = os.path.abspath(".")
texts = []

os_name = platform.system()
if os_name == "Windows":
    if getattr(sys, 'frozen', False):  # 是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = run_path
    ffmpeg_exec = os.path.join(base_path, "ffmpeg.exe")
    cp_exec = "copy"
else:
    ffmpeg_exec = "ffmpeg"
    cp_exec = "cp"
config_path = os.path.join(os.path.expanduser("~"), ".xiaoai")
if not os.path.exists(config_path):
    os.mkdir(config_path)

codes = {
    40006: "音量太大",
    40007: "音量太小",
    40008: "出现了一些小问题",
    40009: "多读了",
}
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


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.result = ''

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


class Iat(object):
    def __init__(self):
        self.STATUS_FIRST_FRAME = 0  # 第一帧的标识
        self.STATUS_CONTINUE_FRAME = 1  # 中间帧标识
        self.STATUS_LAST_FRAME = 2  # 最后一帧的标识
        self.all_result = ''
        self.xunfei_config_path = os.path.join(config_path, "xunfei.conf")
        try:
            f = open(self.xunfei_config_path)
            self.app_id = f.readline().strip()
            self.api_secret = f.readline().strip()
            self.api_key = f.readline().strip()
            self.wsParam = Ws_Param(APPID=self.app_id, APIKey=self.api_key,
                                    APISecret=self.api_secret)
            f.close()
        except FileNotFoundError:
            print("你是第一次使用该功能，需要在讯飞开放平台(https://www.xfyun.cn/)")
            print("注册账户，并新建一个语音听写应用")
            print("然后可以在(https://www.xfyun.cn/services/voicedictation)领取五万次服务包")
            print("然后将控制台的APPID、APISecret、APIKey依次输入")
            input("准备就绪后按回车继续...")
            while True:
                self.app_id = input("请输入讯飞APPID：")
                self.api_secret = input("请输入讯飞APISecret：")
                self.api_key = input("请输入讯飞APIKey：")
                self.wsParam = Ws_Param(APPID=self.app_id, APIKey=self.api_key,
                                        APISecret=self.api_secret)
                wsUrl = self.wsParam.create_url()
                is_ok = [True]
                ws = websocket.WebSocketApp(
                    wsUrl,
                    on_error=lambda ws_, error: is_ok.clear() if "401" in str(error) else is_ok,
                    on_open=lambda ws_: ws_.close()
                )
                ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                if is_ok:
                    f = open(self.xunfei_config_path, "w")
                    f.writelines(self.app_id + "\n")
                    f.writelines(self.api_secret + "\n")
                    f.writelines(self.api_key + "\n")
                    f.close()
                    break
                else:
                    print("输入有误，请重新输入")

    def start(self, audio_file):
        self.all_result = ''

        # 收到websocket消息的处理
        def on_message(ws, message):
            try:
                code = json.loads(message)["code"]
                sid = json.loads(message)["sid"]
                if code != 0:
                    errMsg = json.loads(message)["message"]
                    print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
                    if os.path.exists(self.xunfei_config_path):
                        os.remove(self.xunfei_config_path)

                else:
                    data = json.loads(message)["data"]["result"]["ws"]
                    # print(json.loads(message))
                    result = ""
                    for i in data:
                        for w in i["cw"]:
                            result += w["w"]
                    # print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))
                    print(result, end='')
                    self.all_result += result
            except Exception as e:
                print("receive msg,but parse exception:", e)

        # 收到websocket错误的处理
        def on_error(ws, error):
            print("### error:", error)

        # 收到websocket关闭的处理
        def on_close(ws):
            print("")
            if self.all_result:
                f = open("texts.txt", "a")
                f.writelines(self.all_result + "\n")
                f.close()

        # 收到websocket连接建立的处理
        def on_open(ws):
            def run(*args):
                frameSize = 8000  # 每一帧的音频大小
                intervel = 0.04  # 发送音频间隔(单位:s)
                status = self.STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

                with open(audio_file, "rb") as fp:
                    while True:
                        buf = fp.read(frameSize)
                        # 文件结束
                        if not buf:
                            status = self.STATUS_LAST_FRAME
                        # 第一帧处理
                        # 发送第一帧音频，带business 参数
                        # appid 必须带上，只需第一帧发送
                        if status == self.STATUS_FIRST_FRAME:

                            d = {"common": self.wsParam.CommonArgs,
                                 "business": self.wsParam.BusinessArgs,
                                 "data": {"status": 0, "format": "audio/L16;rate=16000",
                                          "audio": str(base64.b64encode(buf), 'utf-8'),
                                          "encoding": "raw"}}
                            d = json.dumps(d)
                            ws.send(d)
                            status = self.STATUS_CONTINUE_FRAME
                        # 中间帧处理
                        elif status == self.STATUS_CONTINUE_FRAME:
                            d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                          "audio": str(base64.b64encode(buf), 'utf-8'),
                                          "encoding": "raw"}}
                            ws.send(json.dumps(d))
                        # 最后一帧处理
                        elif status == self.STATUS_LAST_FRAME:
                            d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                          "audio": str(base64.b64encode(buf), 'utf-8'),
                                          "encoding": "raw"}}
                            ws.send(json.dumps(d))
                            time.sleep(1)
                            break
                        # 模拟音频采样间隔
                        time.sleep(intervel)
                ws.close()

            thread.start_new_thread(run, ())

        websocket.enableTrace(False)
        wsUrl = self.wsParam.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


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


def process_record():
    print("开始处理声音文件...")
    if not os.path.exists("pcm"):
        os.mkdir("pcm")
    if not os.path.exists("b64"):
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
        os.system("{} *.pcm pcm".format(cp_exec))
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
    files = args if args else range(1, n)
    result_html = open("result.html", "w")
    error_nos = []
    for i in files:
        with open("b64/%s.b64" % i, "r") as f:
            audio_data = f.read()
            asr_data["originText"] = texts[i - 1]
            asr_data["httpAsrRequest"]["asr_audio"] = audio_data
            asr_data["httpAsrRequest"]["request_id"] = ''.join(random.sample(string.ascii_letters + string.digits, 22))
            while True:
                try:
                    resp = requests.post(url="https://speech.ai.xiaomi.com/speech/v1.0/asr/ptts/detect",
                                         json=asr_data,
                                         headers=headers,
                                         timeout=5)
                    break
                except requests.exceptions.RequestException:
                    print("请求超时，正在重试...")
                    continue
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


def upload_record():
    for i in range(1, n):
        with open("b64/%s.b64" % i, "r") as f:
            audio_data = f.read()
            upload_data["audio_data"] = audio_data
            upload_data["request_id"] = ''.join(random.sample(string.ascii_letters + string.digits, 22))
            while True:
                try:
                    resp = requests.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/upload",
                                         json=upload_data,
                                         headers=headers,
                                         timeout=5)
                    if resp.status_code == 200:
                        resp_json = resp.json()
                        if resp_json["code"] == 200:
                            print("第 %s 条上传成功" % i)
                            item = {"url": resp_json["audio_file"], "id": str(i), "text": texts[i - 1]}
                            post_data["train_data_url"].append(item)
                            break
                        else:
                            print("第 %s 条上传失败，resp: %s" % (i, resp.text))
                            print("正在重试...")
                            continue
                    else:
                        print("第 %s 条上传失败，code: %s, resp: %s" % (i, resp.status_code, resp.text))
                        inp = input("是否重试？(yes/no)")
                        if inp == "yes":
                            continue
                        else:
                            break
                except requests.exceptions.RequestException:
                    print("请求超时，正在重试...")
                    continue


def delete():
    while True:
        try:
            resp = requests.get("https://speech.ai.xiaomi.com/speech/v1.0/ptts/list",
                                headers=headers,
                                timeout=5)
            break
        except requests.exceptions.RequestException:
            print("请求超时，正在重试...")
            continue
    resp_json = resp.json()
    models = resp_json["models"]["Owner"]
    i = 1
    delete_data = {"model_name": "",
                   "device_id": ''.join(random.sample(string.ascii_letters + string.digits, 22)),
                   "vendor_id": "",
                   "request_id": "ptts_{}".format(''.join(random.sample(string.ascii_letters + string.digits, 22)))}
    for model in models:
        print("{}. 音色名：{} 状态：{}".format(i, model["name"], model["status"]))
        i += 1

    inp = input("输入序号删除音色，直接回车退出：")
    if inp:
        delete_data["model_name"] = models[int(inp) - 1]["name"]
        delete_data["vendor_id"] = models[int(inp) - 1]["vendor_id"]
        while True:
            try:
                resp = requests.delete("https://speech.ai.xiaomi.com/speech/v1.0/ptts/model",
                                       headers=headers,
                                       json=delete_data,
                                       timeout=5)
                break
            except requests.exceptions.RequestException:
                print("请求超时，正在重试...")
                continue
        if resp.status_code == 200:
            print("删除成功")
        else:
            print("删除失败。")

    pass


def post_record():
    while True:
        inp = input("请选择性别(男生：1，女生：2)：")
        if inp != '1' and inp != '2':
            print("输入错误，请重新输入")
            continue
        post_data["user_gender"] = "male" if inp == '1' else "female"
        break
    while True:
        post_data["model_name"] = input("请输入音色名称：")
        while True:
            try:
                resp = requests.post("https://speech.ai.xiaomi.com/speech/v1.0/ptts/train",
                                     json=post_data,
                                     headers=headers,
                                     timeout=5)
                break
            except requests.exceptions.RequestException:
                print("请求超时，正在重试...")
                continue
        if resp.status_code == 200:
            resp_json = resp.json()
            if int(resp_json["code"]) == 200:
                print("提交成功，请进入小爱音色列表查看")
                break
            else:
                print("提交失败，{} 错误码: {}".format(resp_json["details"], resp_json["code"]))
                if "模型数量" in resp_json["details"]:
                    delete()
                    continue
                else:
                    input("按回车返回重新输入音色名提交...")

        else:
            print("音色提交失败，code: %s, resp: %s" % (resp.status_code, resp.text))
            inp = input("是否重试？（yes/no）:")
            if inp == "yes":
                continue
            else:
                break


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
                inp = input("是否继续使用上次的Authorization？(输入 no 将重新输入Authorization，按回车继续使用上次的Authorization)")
                if inp and inp == "no":
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


def main():
    global texts
    global src_file_type
    global n
    print("本程序仅供技术交流，切勿用于商业用途。\n私自盗用、贩卖由其个人或组织承担相应责任。")
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
    input("准备就绪后按回车继续...")
    while True:
        work_dir = input("请输入工作目录(原始声音文件所在目录的绝对路径，例如：D:\\Data\\lubenwei)：")
        if not work_dir or not os.path.exists(work_dir):
            print("输入的目录不存在！请重新输入。")
            continue
        break
    os.chdir(work_dir)
    while True:
        src_file_type = input("请输入原始文件格式(mp3/wav/m4a/pcm等)：")
        files = [file for file in os.listdir(".") if file.endswith(".{}".format(src_file_type))]
        n = len(files) + 1
        if n > 1:
            files.sort(key=lambda x: int(x.split(".")[0]))
            break
        else:
            print("输入有误，请重新输入")
            continue
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
            inp = input("工作目录下texts.txt不存在，请按要求放入该文件，然后按回车继续"
                        "\n若要执行语音转文本功能，请输入 iat :")
            if inp == "iat":
                open("result.json", "w").close()
                process_record()
                iat = Iat()
                for file in files:
                    iat.start(os.path.join("pcm", file.replace(src_file_type, "pcm")))
                input("语音转文字结果以及保存到texts.txt文件，但是，请务必再次手工校对，校对完成后，按回车继续...")
                while True:
                    inp = input("再次询问，确保你真的对结果进行了校对，如果是，请输入 \"我已校对\": ")
                    if inp == "我已校对":
                        break
            continue

    n = len(texts) + 1
    open("result.json", "w").close()
    get_authorization()
    print("文件准备就绪，开始处理")
    while True:
        process_record()
        verify_record()
        rf = open("result.json", "r")
        args = json.loads(rf.readline().strip()).get("error_nos")
        rf.close()
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
    input("执行结束，按回车关闭窗口。")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
        input("出现未知错误，请截图反馈，然后按任意键退出...")
