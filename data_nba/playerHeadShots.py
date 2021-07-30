import requests
import cv2
import numpy as np
from tqdm import tqdm
import os

f = open('players.txt', 'r')
c = f.readlines()
f.close()

pms = c[0].split('</tr>')[:-1]
pms[0] = pms[0][7:]
for pm in tqdm(pms):
    img_url = pm[pm.index('https'):pm.index('" loading')]
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, np.uint8), 1)

    if 'logoman.png' not in img_url:
        if img is not None:
            pno = img_url.split('/')[-1]
            if os.path.exists('./headshots/%s' % pno):
                cv2.imwrite('./headshots/%s' % pno, img)



