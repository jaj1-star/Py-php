
import os
import sys
import threading
from threading import active_count
import time
import urllib.request
import requests
import pyfiglet

# ===== إعدادات =====
n_threads = 50
threads = []

# ألوان (تشتغل على Python 3)
Z = '\033[1;31m'
F = '\033[2;32m'
Y = '\033[1;33m'

# إدخال المستخدم (Python 3)
link1 = input('ادخل رابط المنشور: ')

# ===== وظائف =====
def view2(proxy):
    channel = link1.split('/')[3]
    msgid = link1.split('/')[4]
    send_seen(channel, msgid, proxy)

def send_seen(channel, msgid, proxy):
    s = requests.Session()
    proxies = {"http": proxy, "https": proxy}
    try:
        r = s.get(f"https://t.me/{channel}/{msgid}", timeout=10, proxies=proxies)
        cookie = r.headers.get('set-cookie', '').split(';')[0]
    except:
        return

def scrap():
    try:
        https = requests.get(
            "https://api.proxyscrape.com/?request=displayproxies&proxytype=https",
            timeout=5
        ).text
        http = requests.get(
            "https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
            timeout=5
        ).text
        with open("proxies.txt", "w") as f:
            f.write(https + "\n" + http)
    except:
        return False
    return True

def checker(proxy):
    view2(proxy)

def start():
    if not scrap():
        return
    with open("proxies.txt") as f:
        proxies = f.read().splitlines()

    for p in proxies:
        if not p:
            continue
        while active_count() > n_threads:
            time.sleep(0.1)
        t = threading.Thread(target=checker, args=(p,))
        t.start()
        threads.append(t)

def process():
    start()

process()
