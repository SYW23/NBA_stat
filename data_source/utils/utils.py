import os
import requests
import pickle

from bs4 import BeautifulSoup


def get_code(url, encoding):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response.encoding = encoding
    return BeautifulSoup(response.text, 'html.parser')


def write2pickle(file, content):
    """
    :param file: 文件名
    :param content: 要写入的内容
    :return:
    """
    with open(file, 'wb') as f:
        pickle.dump(content, f)


def load_pickle(file):
    with open(file, 'rb') as f:
        c = pickle.load(f)
    return c


def walk_dir(path):
    return sorted([x for x in os.listdir(path) if not x.startswith('.')])
