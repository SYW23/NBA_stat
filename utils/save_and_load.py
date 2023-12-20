import pickle


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
