#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Required
- requests (必须)
Info
- author : "xchaoinfo"
- email  : "xchaoinfo@qq.com"
- date   : "2016.4.8"

3.4 遇到一些问题，于 4.8 号解决。
这里遇到的问题是 跨域请求时候， headers 中的 Host 不断变化的问题，需要针对
不同的访问，选择合适的 Host
3.4 遇到问题，大概是忽略了更换 Host 的问题
'''
import requests
import re
import json
import base64
import time
import math
import random
import urllib.request
from PIL import Image
from bs4 import BeautifulSoup
import time
import os
try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus

'''
3.4
所有的请求都分析的好了
模拟请求 一直不成功
在考虑是哪里出了问题
以后学了新的知识后 再来更新
'''

# 构造 Request headers
agent = 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
global headers
headers = {
    "Host": "passport.weibo.cn",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    'User-Agent': agent
}

session = requests.session()
# 访问登录的初始页面
index_url = "https://passport.weibo.cn/signin/login"
session.get(index_url, headers=headers)
urllist_set = set()
image_count = 1


def get_su(username):
    """
    对 email 地址和手机号码 先 javascript 中 encodeURIComponent
    对应 Python 3 中的是 urllib.parse.quote_plus
    然后在 base64 加密后decode
    """
    username_quote = quote_plus(username)
    username_base64 = base64.b64encode(username_quote.encode("utf-8"))
    return username_base64.decode("utf-8")


def login_pre(username):
    # 采用构造参数的方式
    params = {
        "checkpin": "1",
        "entry": "mweibo",
        "su": get_su(username),
        "callback": "jsonpcallback" + str(int(time.time() * 1000) + math.floor(random.random() * 100000))
    }
    '''真是日了狗，下面的这个写成 session.get(login_pre_url，headers=headers) 404 错误
        这条 3.4 号的注释信息，一定是忽略了 host 的变化，真是逗比。
    '''
    pre_url = "https://login.sina.com.cn/sso/prelogin.php"
    headers["Host"] = "login.sina.com.cn"
    headers["Referer"] = index_url
    pre = session.get(pre_url, params=params, headers=headers)
    pa = r'\((.*?)\)'
    res = re.findall(pa, pre.text)
    if res == []:
        print("好像哪里不对了哦，请检查下你的网络，或者你的账号输入是否正常")
    else:
        js = json.loads(res[0])
        if js["showpin"] == 1:
            headers["Host"] = "passport.weibo.cn"
            capt = session.get("https://passport.weibo.cn/captcha/image", headers=headers)
            capt_json = capt.json()
            capt_base64 = capt_json['data']['image'].split("base64,")[1]
            with open('capt.jpg', 'wb') as f:
                f.write(base64.b64decode(capt_base64))
                f.close()
            im = Image.open("capt.jpg")
            im.show()
            im.close()
            cha_code = input("请输入验证码\n>")
            return cha_code, capt_json['data']['pcid']
        else:
            return ""


def login(username, password, pincode):
    postdata = {
        "username": username,
        "password": password,
        "savestate": "1",
        "ec": "0",
        "pagerefer": "",
        "entry": "mweibo",
        "wentry": "",
        "loginfrom": "",
        "client_id": "",
        "code": "",
        "qq": "",
        "hff": "",
        "hfp": "",
    }
    if pincode == "":
        pass
    else:
        postdata["pincode"] = pincode[0]
        postdata["pcid"] = pincode[1]
    headers["Host"] = "passport.weibo.cn"
    headers["Reference"] = index_url
    headers["Origin"] = "https://passport.weibo.cn"
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    post_url = "https://passport.weibo.cn/sso/login"
    login = session.post(post_url, data=postdata, headers=headers)
    # print(login.cookies)
    # print(login.status_code)
    js = login.json()
    # print(js)
    uid = js["data"]["uid"]
    crossdomain = js["data"]["crossdomainlist"]
    cn = "https:" + crossdomain["sina.com.cn"]
    # 下面两个对应不同的登录 weibo.com 还是 m.weibo.cn
    # 一定要注意更改 Host
    # mcn = "https:" + crossdomain["weibo.cn"]
    # com = "https:" + crossdomain['weibo.com']
    headers["Host"] = "login.sina.com.cn"
    session.get(cn, headers=headers)
    headers["Host"] = "weibo.cn"
    ht = session.get("http://weibo.cn/%s/info" % uid, headers=headers)
    # print(ht.url)
    # print(session.cookies)
    pa = r'<title>(.*?)</title>'
    res = re.findall(pa, ht.text)
    # print(ht.text)
    print("你好%s，你正在使用 xchaoinfo 写的模拟登录" % res[0])
    # print(cn, com, mcn)

def get_weibo_data():
    user_id = 1751035982
    url = 'http://weibo.cn/u/%d?filter=1&page=1'%user_id
    ht = session.get(url)
    soup = BeautifulSoup(ht.text, "lxml")
    print(soup.prettify())
    # 总页数
    pageNum = soup.find('input', {'name': 'mp'}).get('value')
    print("total page:",pageNum)

    # 单页url
    for page in range(1,pageNum+1):
        url = 'http://weibo.cn/u/%d?page=%d'%(user_id,page)
        print(url)
        ht = session.get(url)
        soup = BeautifulSoup(ht.text, "lxml")

        # 获取所有微博图片
        urllist = soup.find_all('a',href=re.compile(r'^http://weibo.cn/mblog/oripic',re.I))
        first = 0
        for imgurl in urllist:
            img_get = session.get(imgurl['href'])
            urllist_set.add(img_get.url)

    if not urllist_set:
        print('该页面中不存在图片')
    else:
        #下载图片,保存在当前目录的pythonimg文件夹下
        image_path=os.getcwd()+'/weibo_image'
    if os.path.exists(image_path) is False:
        os.mkdir(image_path)

    x=1
    for imgurl in urllist_set:
        temp= image_path + '/%s.jpg' % x
        print('正在下载第%s张图片' % x)
        try:
            # Download the file from `url` and save it locally under `file_name`:
            with urllib.request.urlopen(imgurl) as response, open(temp, 'wb') as out_file:
                data = response.read() # a `bytes` object
                out_file.write(data)
        except:
            print("该图片下载失败:%s"%imgurl)
        x+=1
    print('微博图片爬取完毕，共%d张，保存路径%s'%(image_count-1,image_path))

if __name__ == "__main__":

    pincode = login_pre(username)
    login(username, password, pincode)
    get_weibo_data()
