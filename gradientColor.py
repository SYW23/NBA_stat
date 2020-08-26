import cv2
import numpy as np

R = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     10, 25, 50, 75, 100, 120, 140, 160, 170, 180, 190, 200, 210, 220]

G = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]

B = [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 250,
     240, 230, 220, 210, 200, 190, 180, 170, 160, 150, 140, 130, 120,
     105, 90, 60, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

X = []

for i in range(len(R)):
    X.append([R[i], G[i], B[i]])
print(X)

cs = [R, G, B]
img = np.zeros((20, 10, 3), np.uint8)
for c in range(3):
    img[:, :, c].fill(cs[c][0])
# img = np.hstack((img, np.zeros((20, 10, 3), np.uint8)))
for i in range(1, len(R)):
    imgTmp = np.zeros((20, 10, 3), np.uint8)
    for c in range(3):
        imgTmp[:, :, c].fill(cs[c][i])
    img = np.hstack((img, imgTmp))
    # img = np.hstack((img, np.zeros((20, 10, 3), np.uint8)))
print(img.shape)
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()


