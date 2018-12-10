# -*- coding:utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('/demo/m3u8/')
import os

from retry import retry
import requests
import datetime
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

import threading

threads = {}


# try_times = threading.local()
@retry(tries=11, delay=5)
def download(url, name, a):
    # print threading.current_thread().getName()
    if not (threading.current_thread().getName() in threads):
        threads[threading.current_thread().getName()] = {}
    threads[threading.current_thread().getName()]["progress"] = "0"
    threads[threading.current_thread().getName()]["name"] = name
    threads[threading.current_thread().getName()]["url"] = url
    if ("times" in threads[threading.current_thread().getName()]):
        threads[threading.current_thread().getName()]["times"] = threads[threading.current_thread().getName()][
                                                                     "times"] + 1
        print "进行尝试第 %d *** %s *** %s ***" % (threads[threading.current_thread().getName()]["times"], name, url)
    else:
        threads[threading.current_thread().getName()]["times"] = 0
        print "第一次下载 %d *** %s *** %s ***" % (threads[threading.current_thread().getName()]["times"], name, url)
    download_path = os.getcwd() + "\download"
    if not os.path.exists(download_path):
        os.mkdir(download_path)

    # 新建日期文件夹
    download_path = download_path + "\\" + name
    # print download_path
    try:
        os.mkdir(download_path)
    except:
        pass
    all_content = requests.get(url).text  # 获取第一层M3U8文件内容
    if "#EXTM3U" not in all_content:
        raise BaseException("非M3U8的链接")
    if "EXT-X-STREAM-INF" in all_content:  # 第一层
        file_line = all_content.split("\n")
        for line in file_line:
            if '.m3u8' in line: url = url.rsplit("/", 1)[
                                          0] + "/" + line  # 拼出第二层m3u8的URLall_content = requests.get(url).text
    file_line = all_content.split("\n")
    unknow = True
    key = ""
    for index, line in enumerate(file_line):  # 第二层
        threads[threading.current_thread().getName()]["progress"] = str(
            (round(index * 1.0 / len(file_line), 2)) * 100) + " %"
        print_progress()
        if "#EXT-X-KEY" in line:  # 找解密Key
            method_pos = line.find("METHOD")
            comma_pos = line.find(",")
            method = line[method_pos:comma_pos].split('=')[1]
            print "Decode Method：", method

            uri_pos = line.find("URI")
            quotation_mark_pos = line.rfind('"')
            key_path = line[uri_pos:quotation_mark_pos].split('"')[1]

            key_url = url.rsplit("/", 1)[0] + "/" + key_path  # 拼出key解密密钥URL
            res = requests.get(key_url)
            key = res.content
            print "key：", key

        if "EXTINF" in line:  # 找ts地址并下载
            unknow = False
            pd_url = url.rsplit("/", 1)[0] + "/" + file_line[index + 1]  # 拼出ts片段的URL
            # print pd_url

            res = requests.get(pd_url)
            c_fule_name = file_line[index + 1].rsplit("/", 1)[-1]

            if len(key):  # AES 解密
                cryptor = AES.new(key, AES.MODE_CBC, key)
                with open(os.path.join(download_path, c_fule_name + ".mp4"), 'ab') as f:
                    f.write(cryptor.decrypt(res.content))
            else:
                with open(os.path.join(download_path, c_fule_name), 'ab') as f:
                    f.write(res.content)
                    f.flush()
    if unknow:
        raise BaseException("未找到对应的下载链接")
    else:
        print "下载完成"
    merge_file(download_path, name)


def print_progress():
    key = threading.current_thread().getName();
    sys.stdout.write("第 %d 次下载 *** %s *** 进度： %s --- url: %s" % (
    threads[key]["times"], threads[key]["name"], threads[key]["progress"], threads[key]["url"]));
    sys.stdout.write("\n");
    # sys.stdout.flush();


def merge_file(path, name):
    os.chdir(path)
    cmd = "copy /b * new.tmp"
    os.system(cmd)
    os.system('del /Q *.ts')
    os.system('del /Q *.mp4')
    os.rename("new.tmp", name + ".mp4")


if __name__ == '__main__':
    # 在这里修改url和文件名 key为url value为文件名
    links = {
        "key":"value"
    }
    for x, y in links.items():
        a = True
        a = 0
        thread = threading.Thread(target=download, args=(x, y, a))
        thread.start()
