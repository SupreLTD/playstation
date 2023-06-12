import random
import time
from datetime import datetime
from typing import List, Any
import grequests
import requests
import re

import schedule
from tqdm import tqdm
from bs4 import BeautifulSoup
from funcy import chunks
import pandas as pd
from django.core.management.base import BaseCommand

from parser.models import Games, DiscountGame, DlcGames, Proxy, Logger, BaseGames, BaseDlcGames
import logging

logging.basicConfig(filename="static/log.txt", level=logging.INFO)


class Parser:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'

    }

    def proxy_checker(self) -> List[dict]:
        url = 'https://store.playstation.com/en-tr/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'

        raw_proxies = [i.proxy for i in Proxy.objects.all()]
        proxies = []

        for i in tqdm(raw_proxies):
            proxy = {'https': i}

            try:
                res = requests.get(url, headers=self.headers, proxies=proxy)
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

    def lir_to_rub(self) -> float:

        try_rub = requests.get('https://www.exchangerates.org.uk/Lira-to-Russian-Roubles-currency-conversion-page.html',
                               headers=self.headers).text
        try_rub = BeautifulSoup(try_rub, 'html.parser').find('span', id='shd2b;').text.replace(',', '.')
        try_rub = float(try_rub)
        return try_rub

    def get_pagination(self, url: str) -> str:
        proxy = self.proxy_checker()
        resp = requests.get(url, headers=self.headers, proxies=random.choice(proxy)).text
        pagination = BeautifulSoup(resp, 'lxml').find('ol',
                                                      class_='psw-l-space-x-1 psw-l-line-center psw-list-style-none').findChildren(
            'span')[-1].text
        return pagination

    def get_games(self, pagination: str, prod: dict) -> tuple[dict[Any, dict[Any, Any]], dict[Any, dict[Any, Any]]]:
        try_rub = self.lir_to_rub()
        games = {}
        games_free = {}
        proxy = self.proxy_checker()

        urls = list(chunks(5, [prod['link'] + str(i) for i in range(1, int(pagination) + 1)]))

        for ur in urls:
            for i in grequests.map(
                    (grequests.get(url, headers=self.headers, proxies=random.choice(proxy)) for url in ur)):
                soup = BeautifulSoup(i.text, 'lxml')
                content = soup.find_all('li', class_='psw-l-w-1/8@desktop')
                for el in content:
                    raw_link = el.find('a')['href']
                    game_id = raw_link.split('/')[-1]

                    try:
                        psplus = 'Да' if el.findChild('span', {
                            'data-qa': 'ems-sdk-grid#productTile4#service-upsell#descriptorText'}).text == 'Extra' else 'Нет'
                    except Exception as e:
                        psplus = 'Нет'
                    eng_title = el.find('span', class_='psw-t-body psw-c-t-1 psw-t-truncate-2 psw-m-b-2').text.replace(
                        'на PS4™', '').replace('на PS5™', '').replace('для PS4™',
                                                                      '').replace(
                        'для PS5™', '').replace('PS4 & PS5', '').replace('(PlayStation®5)', '').replace(
                        '(PlayStation®4)',
                        '').replace(
                        '(PS4™)', '').replace('(PS5™)', '').replace('PS5™', '').replace('PS4™', '')
                    raw_price = el.find('span', class_='psw-m-r-3')
                    price = re.sub(r"[.]", "", raw_price.text.split()[0]).replace(',', '.')
                    if price != 'Unavailable' and price != 'Free' and price != 'Included' and price != 'Game' and price != 'Early':
                        try:
                            full_price = re.sub(r"[.]", "", el.find('s', class_='psw-c-t-2').text.split()[0]).replace(
                                ',',
                                '.')
                        except Exception as e:
                            full_price = price
                        buy_price = int(round(float(price) * try_rub + 150))
                        price = int(float(price) * 5.5 + 150)
                        full_price = int(float(full_price) * 5.5 + 150)
                        # if str(price)[-1] != '0':
                        # price = int(str(price)[:-1] + '0')

                        if int(price) > int(full_price):
                            full_price = int(price)

                        # if str(full_price)[-1] != '0':
                        # full_price = int(str(full_price)[:-1] + '0')
                        # price = float(price) * try_rub
                        # full_price = float(full_price) * try_rub
                        # buy_price = int(round(float(price) * 1.05 + 100))
                        #
                        # if 0 < price < 300:
                        #     price = round(price + 300) + 100
                        # elif 299 < price < 600:
                        #     price = round((price + 200) * 1.3) + 100
                        # elif 599 < price < 1000:
                        #     price = round((price + 150) * 1.5) + 100
                        # else:
                        #     price = round(price * 1.57)
                        #
                        # price += 250
                        #
                        # if price < 750:
                        #     price = 750
                        #
                        # if 0 < full_price < 300:
                        #     full_price = round(full_price + 300) + 100
                        # elif 299 < full_price < 600:
                        #     full_price = round((full_price + 200) * 1.3) + 100
                        # elif 599 < full_price < 1000:
                        #     full_price = round((full_price + 150) * 1.5) + 100
                        # else:
                        #     full_price = round(full_price * 1.57)
                        #
                        # full_price += 250
                        #
                        # if full_price < 750:
                        #     full_price = 750
                        games[game_id] = {}
                        games[game_id]['id'] = game_id
                        games[game_id]['eng_title'] = eng_title
                        games[game_id]['photo'] = el.findChild('img').get('src').split('?')[0]
                        games[game_id]['psplus'] = psplus
                        games[game_id]['price'] = price
                        games[game_id]['full_price'] = full_price
                        games[game_id]['buy_price'] = buy_price
                        games[game_id]['precat'] = prod['cat']

                    else:
                        games_free[game_id] = {}
                        games_free[game_id]['id'] = game_id
                        games_free[game_id]['eng_title'] = eng_title
                        games_free[game_id]['photo'] = el.findChild('img').get('src').split('?')[0]
                        games_free[game_id]['precat'] = prod['cat']
        return games, games_free

    def check_games(self, pagination: str, prod: dict) -> dict:
        games_ids = [i.game_id for i in BaseGames.objects.all()]
        new_games = {}
        proxy = self.proxy_checker()
        urls = list(chunks(5, [prod['link'] + str(i) for i in range(1, int(pagination) + 1)]))
        for ur in tqdm(urls, desc='Check: '):
            for i in grequests.map(
                    (grequests.get(url, headers=self.headers, proxies=random.choice(proxy)) for url in ur)):
                try:
                    soup = BeautifulSoup(i.text, 'lxml')
                    content = soup.find_all('li', class_='psw-l-w-1/8@desktop')
                    for el in content:
                        raw_link = el.find('a')['href']
                        game_id = raw_link.split('/')[-1]
                        if game_id not in games_ids:
                            try:
                                psplus = 'Да' if el.findChild('span', {
                                    'data-qa': 'ems-sdk-grid#productTile4#service-upsell#descriptorText'}).text == 'Extra' else 'Нет'
                            except Exception as e:
                                psplus = 'Нет'
                            eng_title = el.find('span',
                                                class_='psw-t-body psw-c-t-1 psw-t-truncate-2 psw-m-b-2').text.replace(
                                'на PS4™', '').replace('на PS5™', '').replace('для PS4™',
                                                                              '').replace(
                                'для PS5™', '').replace('PS4 & PS5', '').replace('(PlayStation®5)', '').replace(
                                '(PlayStation®4)',
                                '').replace(
                                '(PS4™)', '').replace('(PS5™)', '').replace('PS5™', '').replace('PS4™', '')

                            new_games[game_id] = {}
                            new_games[game_id]['id'] = game_id
                            new_games[game_id]['eng_title'] = eng_title
                            new_games[game_id]['photo'] = el.findChild('img').get('src').split('?')[0]
                            new_games[game_id]['psplus'] = psplus
                            new_games[game_id]['precat'] = prod['cat']
                except Exception as e:
                    continue
        return new_games

    def get_games_data(self, games: dict) -> tuple[dict, dict]:
        proxy = self.proxy_checker()
        games = games
        dlc_games = {}
        data_links = ['https://store.playstation.com/ru-ua/product/' + i['id'] for i in games.values()]
        for data_link in tqdm(list(chunks(1, data_links)), desc='LINKS: '):
            for resp in tqdm(grequests.map(
                    (grequests.get(url, headers=self.headers, proxies=random.choice(proxy)) for url in data_link)),
                    desc='games_data: '):
                try:
                    game_id = resp.url.split('/')[-1]
                    soup = BeautifulSoup(resp.text, 'lxml')
                    try:
                        title = soup.find('h1').text.replace('на PS4™', '').replace('на PS5™', '').replace('для PS4™',
                                                                                                           '').replace(
                            'для PS5™', '').replace('PS4 & PS5', '').replace('(PlayStation®5)', '').replace(
                            '(PlayStation®4)',
                            '').replace(
                            '(PS4™)', '').replace('(PS5™)', '').replace('PS5™', '').replace('PS4™', '')
                        description = soup.find('div', class_='psw-l-w-1/2@desktop').find('p').get_text('\n')
                        background = soup.find('img').get('src').split('?')[0]

                        chars = zip(soup.find_all('dt'), soup.find_all('dd'))
                        voice = lang = False
                        for name, value in chars:
                            if name.text == 'Голос:':
                                voice = True if 'Русский' in value.text else False
                            elif name.text == 'Языки отображения:':
                                lang = True if 'Русский' in value.text else False

                                games[game_id][name.text] = value.text
                            else:
                                games[game_id][name.text] = value.text
                        games[game_id][
                            'local'] = 'Полная локализация' if voice else 'Только субтитры' if lang else 'Нет'
                        games[game_id]['title'] = title
                        games[game_id]['description'] = description
                        games[game_id]['background'] = background
                        try:
                            dlcs = [i for i in soup.find('ul',
                                                         class_='psw-l-gap-y-6 psw-preview-size-s psw-grid-list psw-l-grid').findChildren(
                                'li')]
                            for dlc in dlcs:
                                dlc_id = dlc.find('a')['href'].split('/')[-1]
                                dlc_games[dlc_id] = {}
                                dlc_games[dlc_id]['id'] = dlc_id
                                dlc_games[dlc_id]['rus_game_title'] = title
                                dlc_games[dlc_id]['eng_game_title'] = games[game_id]['eng_title']
                                dlc_games[dlc_id]['photo'] = dlc.find('img')['src']
                                dlc_games[dlc_id]['precat'] = games[game_id]['precat']



                        except Exception as e:

                            pass
                    except Exception as e:
                        logging.error('FIRST: ' + str(e) + ' | ' + str(resp.url))
                        pass

                except Exception as e:
                    logging.error('SECOND: ' + str(e) + str(resp))
                    continue

        return games, dlc_games

    def dlc_parser(self, dlc_res: dict) -> dict:
        proxy = self.proxy_checker()
        games = dlc_res
        dlc_links = ['https://store.playstation.com/en-tr/product/' + i['id'] for i in games.values()]
        for dlc_link in tqdm(list(chunks(1, dlc_links)), desc='DLC_LINKS: '):
            for resp in tqdm(grequests.map(
                    (grequests.get(url, headers=self.headers, proxies=random.choice(proxy)) for url in dlc_link)),
                    desc='dlc_games: '):
                try:
                    game_id = resp.url.split('/')[-1]
                    soup = BeautifulSoup(resp.text, 'lxml')
                    try:
                        title = soup.find('h1').text.replace('на PS4™', '').replace('на PS5™', '').replace('для PS4™',
                                                                                                           '').replace(
                            'для PS5™', '').replace('PS4 & PS5', '').replace('(PlayStation®5)', '').replace(
                            '(PlayStation®4)',
                            '').replace(
                            '(PS4™)', '').replace('(PS5™)', '').replace('PS5™', '').replace('PS4™', '')

                        games[game_id]['eng_title'] = title

                    except Exception as e:
                        pass
                except Exception as e:
                    continue
        return games

    def db_insert_games(self, games: dict) -> None:

        for i in tqdm(games.values(), desc=f'Save: '):
            try:
                game_id = i['id']
            except Exception as e:
                game_id = ''
            try:
                name = i['title']
            except Exception as e:
                name = ''
            try:
                eng_name = i['eng_title']
            except Exception as e:
                eng_name = ''
            try:
                description = i['description']
            except Exception as e:
                description = ''
            try:
                cat = i['precat']
            except Exception as e:
                cat = ''
            try:
                pspl = i['psplus']
            except Exception as e:
                pspl = ''
            try:
                lang = i['Языки отображения:']
            except Exception as e:
                lang = ''
            try:
                photo = i['photo']
            except Exception as e:
                photo = ''
            try:
                background = i['background']
            except Exception as e:
                background = ''
            try:
                platform = i['Платформа:']
            except Exception as e:
                platform = ''
            try:
                realise = i['Выпуск:']
            except Exception as e:
                realise = ''
            try:
                author = i['Издатель:']
            except Exception as e:
                author = ''
            try:
                genre = i['Жанр:']
            except Exception as e:
                genre = ''
            try:
                local = i['local']
            except Exception as e:
                local = ''

            BaseGames.objects.create(
                game_id=game_id,
                name=name,
                eng_name=eng_name,

                description=description,
                cat=cat,
                pspl=pspl,
                lang=lang,
                local=local,
                photo=photo,
                background=background,
                platform=platform,
                realise=realise,
                author=author,
                genre=genre
            )

    def db_insert_dls_games(self, games: dict) -> None:

        for i in tqdm(games.values(), desc='Save DLC: '):
            try:
                game_id = i['id']
            except Exception as e:
                game_id = ''
            try:
                name = i['title']
            except Exception as e:
                name = ''
            try:
                eng_name = i['eng_title']
            except Exception as e:
                eng_name = ''

            try:
                description = i['description']
            except Exception as e:
                description = ''
            try:
                cat = i['precat']
            except Exception as e:
                cat = ''
            try:
                pspl = i['psplus']
            except Exception as e:
                pspl = ''
            try:
                lang = i['Языки отображения:']
            except Exception as e:
                lang = ''
            try:
                photo = i['photo']
            except Exception as e:
                photo = ''
            try:
                background = i['background']
            except Exception as e:
                background = ''
            try:
                platform = i['Платформа:']
            except Exception as e:
                platform = ''
            try:
                realise = i['Выпуск:']
            except Exception as e:
                realise = ''
            try:
                author = i['Издатель:']
            except Exception as e:
                author = ''
            try:
                genre = i['Жанр:']
            except Exception as e:
                genre = ''
            try:
                eng_game = i['eng_game_title']
            except Exception as e:
                eng_game = ''
            try:
                rus_game = i['rus_game_title']
            except Exception as e:
                rus_game = ''
            try:
                local = i['local']
            except Exception as e:
                local = ''

            BaseDlcGames.objects.create(
                game_id=game_id,
                name=name,
                eng_name=eng_name,
                eng_game=eng_game,
                rus_game=rus_game,

                description=description,
                cat=cat,
                pspl=pspl,
                lang=lang,
                local=local,
                photo=photo,
                background=background,
                platform=platform,
                realise=realise,
                author=author,
                genre=genre
            )

    def games(self) -> None:
        proxy = self.proxy_checker()
        try_rub = self.lir_to_rub()
        ids = [i.game_id for i in BaseGames.objects.all()]
        urls = list(chunks(50, [
            f'https://web.np.playstation.com/api/graphql/v1//op?operationName=queryRetrieveTelemetryDataPDPProduct&variables=%7B%22conceptId%22%3Anull%2C%22productId%22%3A%22{i}%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22163ce11323f3618e7a2fb5ef467db2f7f02ddade88218a83b5b414f1f65cfdce%22%7D%7D'
            for i in ids]))
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://store.playstation.com/',
            'content-type': 'application/json',
            'X-PSN-Store-Locale-Override': 'en-tr',
            'X-PSN-App-Ver': '@sie-ppr-web-store/app/@sie-ppr-web-store/app@0.73.0-c7815359c8ba5c8a5528f80ef27f4c59dd11f706',
            'X-PSN-Correlation-Id': '416c447a-bf35-45fb-b02c-a08127551c23',
            'apollographql-client-name': '@sie-ppr-web-store/app',
            'apollographql-client-version': '@sie-ppr-web-store/app@0.73.0',
            'X-PSN-Request-Id': '44bd85bb-ff2f-4d50-a0ce-7f2c369fba12',
            'Origin': 'https://store.playstation.com',
            'Connection': 'keep-alive',
            # 'Cookie': 'AMCV_BD260C0F53C9733E0A490D45%40AdobeOrg=-1124106680%7CMCIDTS%7C19463%7CMCMID%7C69347127103841178506584738935727179766%7CMCAID%7CNONE%7CMCOPTOUT-1681554358s%7CNONE%7CvVersion%7C5.2.0; s_fid=54A6A93250FCAE6B-240D963C891EB567; _abck=72DFB0A690A7AC3ABB1A762B03670828~-1~YAAQbmReaCLMgHyHAQAAPxv8hAl9qhSuJGiSMWHR24dXMVTNjC5DV0bFwQa/iOvEDpTQWwbl62fuK6npV9cDo4isPcEUiPD3ePzmorofv/fNk7foXh91BvPY9NnlW4q5B2vQI/KCyGsQrbEyxZv+qk4KZMMnig2LCMDmzDz1ay51m1k0zckq3V9iw4YbpYdfyLJpIw+p00RqPpYP/f0bZ+vlnJ7Pml94NCtRhJYL7S8Otw6V8FpUPu1PKb8xcPA6ZQVK3/d99a8inm6cpHZMVBzcignfoIFOMA3YrFnGpOFmNj8aKd8fnH1vOmGW/oPKxqESL0Cd0o7TWU5GsRkpukq3aliAyWBLHh4Wqqog6gF3+A78TpJmcjtACs27bUAgk/QDH7bg7sXC8hDeux3bcQ8I6uE6Tr3XKOKNhSC3vDf1+f7POzcVKee6/MWpX3vWG4310OHcyvw3+qaJA2omT2w/eQd+wbAwqwqhzna0FVI=~-1~-1~-1; bm_sz=1A065D24272BCF45DA9CF9C307AAE17F~YAAQbmReaCPMgHyHAQAAPxv8hBMy0FYC/8Srw2IG3+ETYHcV8e0zchprps52EAi7fH2BoJJ4MAPZAtW0ANS/Mpyrxld9f0Mlngroc0/gp3viEa0pOIQTeTG0tPFFNSyij14uBHvwulsqKtW3yixEBBPBsZb4FnOS9EhjLOflUjQoOSRgpPAPyN2WlvPCTEdrw4ZP1+sy3yVTizIwFwVlMNlMMakBDlC2ZRsFkM9kuKviQK/y5Fxiga036iPjfVioNkbWygTJrUnNejFOU1EwB7EZzXLBHND2vOW8y280A/zgWKTvDfQPYK3h31InjoZmU+KVPwoHiVAdb8zZdzE6KhmvZuJ+y0CsoJzenUp+pFq5ZySXHTX8z53xfLPdI1vUa4pToIqAh19ohBtj1PeyA6nXYe0ThEB2bAdT0WYcAK68i6gq6qUINbpYd2J0IQT8HCgOcdEnvGTyURyeKE3e0SwUYhNFq7AD57H5W5igyEXFBtWye/BVMrhfs3BikjLNIELN~3293762~3686711',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            # Requests doesn't support trailers
            # 'TE': 'trailers',
        }
        for ur in tqdm(urls, desc='Games_LINKS: '):
            for resp in grequests.map(
                    (grequests.get(url, headers=headers, proxies=random.choice(proxy)) for url in ur)):
                try:
                    data = resp.json()
                    id_ = data['data']['productRetrieve']['id']
                    # full_price = re.sub(r"[.]", "",
                    #                     data['data']['productRetrieve']['webctas'][0]['price']['basePrice'].split()[
                    #                         0]).replace(
                    #     ',', '.')
                    # price = re.sub(r"[.]", "",
                    #                data['data']['productRetrieve']['webctas'][0]['price']['discountedPrice'].split()[
                    #                    0]).replace(',', '.')
                    if len(data['data']['productRetrieve']['webctas']) == 1:

                        full_price = re.sub(r"[.]", "",
                                            data['data']['productRetrieve']['webctas'][0]['price']['basePrice'].split()[
                                                0]).replace(
                            ',', '.')
                        price = re.sub(r"[.]", "",
                                       data['data']['productRetrieve']['webctas'][0]['price'][
                                           'discountedPrice'].split()[
                                           0]).replace(',', '.')
                    else:
                        if re.sub(r"[.]", "",
                                  data['data']['productRetrieve']['webctas'][0]['price']['discountedPrice'].split()[
                                      0]).replace(',', '.')[:-3].isdigit():
                            full_price = re.sub(r"[.]", "",
                                                data['data']['productRetrieve']['webctas'][0]['price'][
                                                    'basePrice'].split()[
                                                    0]).replace(
                                ',', '.')
                            price = re.sub(r"[.]", "",
                                           data['data']['productRetrieve']['webctas'][0]['price'][
                                               'discountedPrice'].split()[
                                               0]).replace(',', '.')
                        else:
                            full_price = re.sub(r"[.]", "",
                                                data['data']['productRetrieve']['webctas'][1]['price'][
                                                    'basePrice'].split()[
                                                    0]).replace(
                                ',', '.')
                            price = re.sub(r"[.]", "",
                                           data['data']['productRetrieve']['webctas'][1]['price'][
                                               'discountedPrice'].split()[
                                               0]).replace(',', '.')

                    if int(price) < 1:
                        continue
                    pspl = 'Нет'
                    for pl in data['data']['productRetrieve']['webctas']:
                        if 'PS_PLUS' in pl['price']['serviceBranding'] and pl['price']['discountedPrice'] == 'Included':
                            pspl = 'Да'
                    if price != 'Unavailable' and price != 'Free' and price != 'Included' and price != 'Game' and price != 'Early' and price != None:
                        # price = float(price) * try_rub
                        # full_price = float(full_price) * try_rub
                        # buy_price = int(round(float(price) * 1.05 + 100))

                        buy_price = int(round(float(price) * try_rub + 150))
                        price = int(float(price) * 5.5 + 150)
                        full_price = int(float(full_price) * 5.5 + 150)
                        # full_price = int(float(full_price) * try_rub)
                        # if str(price)[-1] != '0':
                        # price = int(str(price)[:-1] + '0')

                        if int(price) > int(full_price):
                            full_price = int(price)

                        # if str(full_price)[-1] != '0':
                        # full_price = int(str(full_price)[:-1] + '0')
                        # if 0 < price < 300:
                        #     price = round(price + 300) + 100
                        # elif 299 < price < 600:
                        #     price = round((price + 200) * 1.3) + 100
                        # elif 599 < price < 1000:
                        #     price = round((price + 150) * 1.5) + 100
                        # else:
                        #     price = round(price * 1.57)
                        #
                        # price += 250
                        #
                        # if price < 750:
                        #     price = 750
                        #
                        # if 0 < full_price < 300:
                        #     full_price = round(full_price + 300) + 100
                        # elif 299 < full_price < 600:
                        #     full_price = round((full_price + 200) * 1.3) + 100
                        # elif 599 < full_price < 1000:
                        #     full_price = round((full_price + 150) * 1.5) + 100
                        # else:
                        #     full_price = round(full_price * 1.57)
                        #
                        # full_price += 250
                        #
                        # if full_price < 750:
                        #     full_price = 750

                        game = BaseGames.objects.get(game_id=id_)
                        Games.objects.create(
                            game_id=id_,
                            name=game.name,
                            eng_name=game.eng_name,

                            description=game.description,
                            cat=game.cat,
                            pspl=pspl,
                            lang=game.lang,
                            local=game.local,
                            photo=game.photo,
                            background=game.background,
                            platform=game.platform,
                            realise=game.realise,
                            author=game.author,
                            genre=game.genre,
                            price=price,
                            full_price=full_price,
                            buy_price=buy_price
                        )
                except Exception as e:
                    continue

    def dlc_games(self) -> None:
        proxy = self.proxy_checker()
        try_rub = self.lir_to_rub()
        ids = [i.game_id for i in BaseDlcGames.objects.all()]
        urls = list(chunks(50, [
            f'https://web.np.playstation.com/api/graphql/v1//op?operationName=queryRetrieveTelemetryDataPDPProduct&variables=%7B%22conceptId%22%3Anull%2C%22productId%22%3A%22{i}%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22163ce11323f3618e7a2fb5ef467db2f7f02ddade88218a83b5b414f1f65cfdce%22%7D%7D'
            for i in ids]))
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://store.playstation.com/',
            'content-type': 'application/json',
            'X-PSN-Store-Locale-Override': 'en-tr',
            'X-PSN-App-Ver': '@sie-ppr-web-store/app/@sie-ppr-web-store/app@0.73.0-c7815359c8ba5c8a5528f80ef27f4c59dd11f706',
            'X-PSN-Correlation-Id': '416c447a-bf35-45fb-b02c-a08127551c23',
            'apollographql-client-name': '@sie-ppr-web-store/app',
            'apollographql-client-version': '@sie-ppr-web-store/app@0.73.0',
            'X-PSN-Request-Id': '44bd85bb-ff2f-4d50-a0ce-7f2c369fba12',
            'Origin': 'https://store.playstation.com',
            'Connection': 'keep-alive',
            # 'Cookie': 'AMCV_BD260C0F53C9733E0A490D45%40AdobeOrg=-1124106680%7CMCIDTS%7C19463%7CMCMID%7C69347127103841178506584738935727179766%7CMCAID%7CNONE%7CMCOPTOUT-1681554358s%7CNONE%7CvVersion%7C5.2.0; s_fid=54A6A93250FCAE6B-240D963C891EB567; _abck=72DFB0A690A7AC3ABB1A762B03670828~-1~YAAQbmReaCLMgHyHAQAAPxv8hAl9qhSuJGiSMWHR24dXMVTNjC5DV0bFwQa/iOvEDpTQWwbl62fuK6npV9cDo4isPcEUiPD3ePzmorofv/fNk7foXh91BvPY9NnlW4q5B2vQI/KCyGsQrbEyxZv+qk4KZMMnig2LCMDmzDz1ay51m1k0zckq3V9iw4YbpYdfyLJpIw+p00RqPpYP/f0bZ+vlnJ7Pml94NCtRhJYL7S8Otw6V8FpUPu1PKb8xcPA6ZQVK3/d99a8inm6cpHZMVBzcignfoIFOMA3YrFnGpOFmNj8aKd8fnH1vOmGW/oPKxqESL0Cd0o7TWU5GsRkpukq3aliAyWBLHh4Wqqog6gF3+A78TpJmcjtACs27bUAgk/QDH7bg7sXC8hDeux3bcQ8I6uE6Tr3XKOKNhSC3vDf1+f7POzcVKee6/MWpX3vWG4310OHcyvw3+qaJA2omT2w/eQd+wbAwqwqhzna0FVI=~-1~-1~-1; bm_sz=1A065D24272BCF45DA9CF9C307AAE17F~YAAQbmReaCPMgHyHAQAAPxv8hBMy0FYC/8Srw2IG3+ETYHcV8e0zchprps52EAi7fH2BoJJ4MAPZAtW0ANS/Mpyrxld9f0Mlngroc0/gp3viEa0pOIQTeTG0tPFFNSyij14uBHvwulsqKtW3yixEBBPBsZb4FnOS9EhjLOflUjQoOSRgpPAPyN2WlvPCTEdrw4ZP1+sy3yVTizIwFwVlMNlMMakBDlC2ZRsFkM9kuKviQK/y5Fxiga036iPjfVioNkbWygTJrUnNejFOU1EwB7EZzXLBHND2vOW8y280A/zgWKTvDfQPYK3h31InjoZmU+KVPwoHiVAdb8zZdzE6KhmvZuJ+y0CsoJzenUp+pFq5ZySXHTX8z53xfLPdI1vUa4pToIqAh19ohBtj1PeyA6nXYe0ThEB2bAdT0WYcAK68i6gq6qUINbpYd2J0IQT8HCgOcdEnvGTyURyeKE3e0SwUYhNFq7AD57H5W5igyEXFBtWye/BVMrhfs3BikjLNIELN~3293762~3686711',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            # Requests doesn't support trailers
            # 'TE': 'trailers',
        }
        for ur in tqdm(urls, desc='DLS_LINKS: '):
            for resp in tqdm(grequests.map(
                    (grequests.get(url, headers=headers, proxies=random.choice(proxy)) for url in ur)),
                    desc='dlc_games: '):
                try:
                    data = resp.json()
                    id_ = data['data']['productRetrieve']['id']

                    if len(data['data']['productRetrieve']['webctas']) == 1:

                        full_price = re.sub(r"[.]", "",
                                            data['data']['productRetrieve']['webctas'][0]['price']['basePrice'].split()[
                                                0]).replace(
                            ',', '.')
                        price = re.sub(r"[.]", "",
                                       data['data']['productRetrieve']['webctas'][0]['price'][
                                           'discountedPrice'].split()[
                                           0]).replace(',', '.')
                    else:
                        if re.sub(r"[.]", "",
                                  data['data']['productRetrieve']['webctas'][0]['price']['discountedPrice'].split()[
                                      0]).replace(',', '.')[:-3].isdigit():
                            full_price = re.sub(r"[.]", "",
                                                data['data']['productRetrieve']['webctas'][0]['price'][
                                                    'basePrice'].split()[
                                                    0]).replace(
                                ',', '.')
                            price = re.sub(r"[.]", "",
                                           data['data']['productRetrieve']['webctas'][0]['price'][
                                               'discountedPrice'].split()[
                                               0]).replace(',', '.')
                        else:
                            full_price = re.sub(r"[.]", "",
                                                data['data']['productRetrieve']['webctas'][1]['price'][
                                                    'basePrice'].split()[
                                                    0]).replace(
                                ',', '.')
                            price = re.sub(r"[.]", "",
                                           data['data']['productRetrieve']['webctas'][1]['price'][
                                               'discountedPrice'].split()[
                                               0]).replace(',', '.')

                    pspl = 'Нет'
                    for pl in data['data']['productRetrieve']['webctas']:
                        if 'PS_PLUS' in pl['price']['serviceBranding'] and pl['price']['discountedPrice'] == 'Included':
                            pspl = 'Да'

                    if price != 'Unavailable' and price != 'Free' and price != 'Included' and price != 'Game' and price != 'Early' and price != None:
                        # price = float(price) * try_rub
                        # full_price = float(full_price) * try_rub
                        # buy_price = int(round(float(price) * 1.05 + 100))
                        #
                        # if 0 < price < 300:
                        #     price = round(price + 300) + 100
                        # elif 299 < price < 600:
                        #     price = round((price + 200) * 1.3) + 100
                        # elif 599 < price < 1000:
                        #     price = round((price + 150) * 1.5) + 100
                        # else:
                        #     price = round(price * 1.57)
                        #
                        # price += 250
                        #
                        # if price < 750:
                        #     price = 750
                        #
                        # if 0 < full_price < 300:
                        #     full_price = round(full_price + 300) + 100
                        # elif 299 < full_price < 600:
                        #     full_price = round((full_price + 200) * 1.3) + 100
                        # elif 599 < full_price < 1000:
                        #     full_price = round((full_price + 150) * 1.5) + 100
                        # else:
                        #     full_price = round(full_price * 1.57)
                        #
                        # full_price += 250
                        #
                        # if full_price < 750:
                        #     full_price = 750

                        buy_price = int(round(float(price) * try_rub + 150))
                        price = int(float(price) * 5.5 + 150)
                        full_price = int(float(full_price) * 5.5 + 150)
                        # if str(price)[-1] != '0':
                        # price = int(str(price)[:-1] + '0')

                        if int(price) > int(full_price):
                            full_price = int(price)

                        # if str(full_price)[-1] != '0':
                        # full_price = int(str(full_price)[:-1] + '0')

                        game = BaseDlcGames.objects.get(game_id=id_)
                        DlcGames.objects.create(
                            game_id=id_,
                            name=game.name,
                            eng_name=game.eng_name,
                            eng_game=game.eng_game,
                            rus_game=game.rus_game,
                            description=game.description,
                            cat=game.cat,
                            pspl=pspl,
                            lang=game.lang,
                            local=game.local,
                            photo=game.photo,
                            background=game.background,
                            platform=game.platform,
                            realise=game.realise,
                            author=game.author,
                            genre=game.genre,
                            price=price,
                            full_price=full_price,
                            buy_price=buy_price

                        )
                except Exception as e:
                    continue

    def db_dis_insert_games(self, games: dict) -> None:

        for i in tqdm(games.values(), desc=f'Save: '):
            try:
                game_id = i['id']
            except Exception as e:
                game_id = ''
            try:
                name = i['title']
            except Exception as e:
                name = ''
            try:
                eng_name = i['eng_title']
            except Exception as e:
                eng_name = ''
            try:
                price = i['price']
            except Exception as e:
                price = ''
            try:
                full_price = i['full_price']
            except Exception as e:
                full_price = ''
            try:
                buy_price = i['buy_price']
            except Exception as e:
                buy_price = ''
            try:
                description = i['description']
            except Exception as e:
                description = ''
            try:
                cat = i['precat']
            except Exception as e:
                cat = ''
            try:
                pspl = i['psplus']
            except Exception as e:
                pspl = ''
            try:
                lang = i['Языки отображения:']
            except Exception as e:
                lang = ''
            try:
                photo = i['photo']
            except Exception as e:
                photo = ''
            try:
                background = i['background']
            except Exception as e:
                background = ''
            try:
                platform = i['Платформа:']
            except Exception as e:
                platform = ''
            try:
                realise = i['Выпуск:']
            except Exception as e:
                realise = ''
            try:
                author = i['Издатель:']
            except Exception as e:
                author = ''
            try:
                genre = i['Жанр:']
            except Exception as e:
                genre = ''
            try:
                local = i['local']
            except Exception as e:
                local = ''
            if price:
                DiscountGame.objects.create(
                    game_id=game_id,
                    name=name,
                    eng_name=eng_name,
                    price=price,
                    full_price=full_price,
                    buy_price=buy_price,
                    description=description,
                    cat=cat,
                    pspl=pspl,
                    lang=lang,
                    local=local,
                    photo=photo,
                    background=background,
                    platform=platform,
                    realise=realise,
                    author=author,
                    genre=genre
                )

    def write_dls_games(self) -> None:
        columns = ['Название', 'Оригинальное название', 'Название игры', 'Оригинальное название игры', 'Описание',
                   'Цена', 'Цена без скидки', 'Цена закупки',
                   'Подкаталог',
                   'PlayStation Plus', 'Русский язык', 'Фото', 'Background', 'Платформа', 'Выпуск', 'Издатель',
                   'Жанр', 'Язык']
        games = DlcGames.objects.all()
        data = [[i.name, i.eng_name, i.eng_game, i.rus_game, i.description, i.price, i.full_price, i.buy_price, i.cat,
                 i.pspl, i.local, i.photo,
                 i.background, i.platform, i.realise, i.author, i.genre, i.lang] for i in games]

        df = pd.DataFrame(data, columns=columns)
        df.to_csv(fr'static/Dlc_games.csv', index=False)

    def write_games(self, name: str) -> None:
        if name == 'Games':
            games = Games.objects.all()
        else:
            games = DiscountGame.objects.all()
        columns = ['Название', 'Оригинальное название', 'Описание', 'Цена', 'Цена без скидки', 'Цена закупки',
                   'Подкаталог',
                   'PlayStation Plus', 'Русский язык', 'Фото', 'Background', 'Платформа', 'Выпуск', 'Издатель',
                   'Жанр', 'Язык']
        data = [[i.name, i.eng_name, i.description, i.price, i.full_price, i.buy_price, i.cat, i.pspl, i.local, i.photo,
                 i.background, i.platform, i.realise, i.author, i.genre, i.lang] for i in games]
        df = pd.DataFrame(data, columns=columns)
        df.to_csv(fr'static/{name}.csv', index=False)

    def dis_run(self) -> None:
        dis = {'cat': 'Предложения',
               'link': 'https://store.playstation.com/en-tr/category/803cee19-e5a1-4d59-a463-0b6b2701bf7c/'}

        pag = self.get_pagination(dis['link'])
        data = self.get_games(pag, dis)
        res = self.get_games_data(data[0])
        self.db_dis_insert_games(res[0])

    def run(self) -> None:
        start = datetime.now().replace(microsecond=0)
        Games.objects.all().delete()
        DlcGames.objects.all().delete()
        DiscountGame.objects.all().delete()
        ps4 = {'cat': 'PS4',
               'link': 'https://store.playstation.com/en-tr/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/'}
        pag_1 = self.get_pagination(ps4['link'])
        check_1 = self.check_games(pag_1, ps4)
        if len(check_1) > 0:
            result1 = self.get_games_data(check_1)
            games = result1[0]
            dlc = self.get_games_data(self.dlc_parser(result1[1]))[0]
            self.db_insert_games(games)
            self.db_insert_dls_games(dlc)
        ps5 = {'cat': 'PS5',
               'link': 'https://store.playstation.com/en-tr/category/4cbf39e2-5749-4970-ba81-93a489e4570c/'}
        pag_2 = self.get_pagination(ps5['link'])
        check_2 = self.check_games(pag_2, ps5)
        if len(check_2) > 0:
            result2 = self.get_games_data(check_2)
            games = result2[0]
            dlc = self.get_games_data(self.dlc_parser(result2[1]))[0]
            self.db_insert_games(games)
            self.db_insert_dls_games(dlc)
        self.games()
        self.dlc_games()
        self.write_games('Games')
        self.write_dls_games()
        self.dis_run()
        self.write_games('Dis_games')
        with open('static/proxies.txt', 'r') as f:
            proxies = ''.join(f.readlines())
        count_games = len(Games.objects.all())
        count_dlc = len(DlcGames.objects.all())
        count_dis = len(DiscountGame.objects.all())
        finish = datetime.now().replace(microsecond=0)
        Logger.objects.create(start=start, finish=finish, count_games=count_games, count_dlc=count_dlc,
                              count_discount=count_dis, proxies=proxies)


class Command(BaseCommand):
    help = 'PS_Parser_db'

    def handle(self, *args, **options):
        res = Parser()

        schedule.every().day.at('03:30').do(res.run)
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(e)
                time.sleep(1)
                continue
