import random
import time
from datetime import datetime
from typing import List

import grequests
import requests
import re

import schedule
from tqdm import tqdm
from bs4 import BeautifulSoup
from funcy import chunks
import pandas as pd
from django.core.management.base import BaseCommand

from parser.models import BaseGames, BaseDlcGames, Proxy

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'

}


def proxy_checker() -> List[dict]:
    url = 'https://store.playstation.com/en-tr/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'

    raw_proxies = [i.proxy for i in Proxy.objects.all()]
    proxies = []

    for i in tqdm(raw_proxies):
        proxy = {'https': i}

        try:
            res = requests.get(url, headers=headers, proxies=proxy)
            if res.status_code == 200:
                proxies.append(i + '\n')
        except Exception as e:
            continue
    with open('static/proxies.txt', 'w') as f:
        for i in proxies:
            f.write(i)
    print('Proxy checked')
    with open('static/proxies.txt', 'r', encoding='utf-8') as file:
        proxies = [{'https': proxy.removesuffix('\n')} for proxy in file.readlines()]
    if len(proxies) == 0:
        proxies.append({'https': ''})
    return proxies


def localisation() -> None:
    proxy = proxy_checker()
    ids = list(chunks(100, [i.game_id for i in BaseGames.objects.all()]))
    for urls in tqdm(ids):
        for item in tqdm(urls):
            url = 'https://store.playstation.com/ru-ua/product/' + item
            try:
                response = requests.get(url, headers=headers, proxies=random.choice(proxy)).text
                soup = BeautifulSoup(response, 'lxml')
                chars = zip(soup.find_all('dt'), soup.find_all('dd'))
                voice = lang = False
                for name, value in chars:
                    if name.text == 'Голос:':
                        voice = True if 'Русский' in value.text else False
                    elif name.text == 'Языки отображения:':
                        lang = True if 'Русский' in value.text else False

                BaseGames.objects.filter(game_id=item).update(
                    local='Полная локализация' if voice else 'Только субтитры' if lang else 'Нет')

            except Exception as e:
                continue


class Command(BaseCommand):
    help = 'local'

    def handle(self, *args, **options):
        localisation()
