import sys

sys.path.append('../')
from util import LoadPickle, writeToPickle
import numpy as np
from keras import models
from keras import layers
from keras import optimizers
from keras.callbacks import EarlyStopping, CSVLogger, ModelCheckpoint
from keras.models import load_model
from keras.optimizers import Adam
import keras.backend as K
from keras.callbacks import LearningRateScheduler
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn.ensemble import GradientBoostingClassifier, AdaBoostRegressor
from sklearn.model_selection import GridSearchCV
from sklearn import metrics

plt.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def normalization(data, method='min-max'):
    if method == 'min-max':
        minn = np.min(data)
        maxx = np.max(data)
        return (data - minn) / (maxx - minn)
    elif method == 'z-score':
        ave = np.average(data)
        std = np.std(data)
        return (data - ave) / std
    elif method == 'max':
        absmax = np.max(data)
        # print(absmax)
        return data / absmax
    else:
        return None


# 学习率调整
def scheduler(epoch):
    # 每隔100个epoch，学习率减小为原来的1/10
    if epoch % 10 == 0 and epoch != 0:
        lr = K.get_value(model.optimizer.lr)
        K.set_value(model.optimizer.lr, lr * 0.1)
        print("lr changed to {}".format(lr * 0.1))
    return K.get_value(model.optimizer.lr)


def gen(inputs=None, targets=None, batch_size=None, shuffle=False):
    while True:
        assert len(inputs) == len(targets)
        if shuffle:
            indices = np.arange(len(inputs))
            np.random.shuffle(indices)
        for start_idx in range(0, len(inputs) - batch_size + 1, batch_size):
            if shuffle:
                excerpt = indices[start_idx:start_idx + batch_size]
            else:
                excerpt = slice(start_idx, start_idx + batch_size)
            yield inputs[excerpt], targets[excerpt]


def resultPresentation(res, Y):
    accuracy = np.sum((res - Y) == 0) / Y.shape[0] * 100
    precision = np.sum((Y == 1) & (res == 1)) / np.sum(res == 1) * 100
    recall = np.sum((Y == 1) & (res == 1)) / np.sum(Y) * 100
    F1_score = 2 * precision * recall / (precision + recall)
    print('准确率', accuracy, '%')
    print('精确率', precision, '%')
    print('召回率', recall, '%')
    print('F1分数', F1_score, '%')


# ====================数据准备====================
# 读取数据
data = LoadPickle('mvp_share_training_data.pickle')
# print(data[0])
print('数据总量:', data[0].shape)
print('有值数据数量:', np.sum(data[1] > 0), '占比:', np.sum(data[1] > 0) / data[0].shape[0] * 100, '%')

# # 数据标准化
# ave = np.average(data[0])
# std = np.std(data[0])
# data[0] = normalization(data[0], method='max')
# Y_binary = np.where(data[1] > 0, 1, 0)
#
# # 划分数据集
# train_indexes = (data[2] != '2019_2020') & (data[2] != '2020_2021')
# val_indexes = (data[2] == '2019_2020')
# test_indexes = (data[2] == '2020_2021')
#
# X_train = data[0][train_indexes]
# Y_train = Y_binary[train_indexes]
# X_val = data[0][val_indexes]
# Y_val = Y_binary[val_indexes]
# X_test = data[0][test_indexes]
# Y_test = Y_binary[test_indexes]
# print('训练数据:', X_train.shape, Y_train.shape)
# print('验证数据:', X_val.shape, Y_val.shape)
# print('测试数据:', X_test.shape, Y_test.shape)
#
# # ====================网络搭建====================
# model = models.Sequential()
# model.add(layers.Dense(256, input_shape=(data[0].shape[1], ), activation='relu'))
# # model.add(layers.Dropout(0.2))
# model.add(layers.Dense(128, activation='relu'))
# model.add(layers.Dropout(0.2))
# model.add(layers.Dense(1, activation='sigmoid'))
# print(model.summary())
#
# model.compile(optimizer=Adam(1e-2), loss='binary_crossentropy', metrics=['accuracy'])
# batch_size = 8
# epochs = 50
# callbacks = [EarlyStopping(monitor='val_loss', patience=20, verbose=2), CSVLogger('best_model.csv'), LearningRateScheduler(scheduler)]
# model.fit_generator(gen(X_train, Y_train, batch_size=batch_size, shuffle=True), epochs=epochs,
#                     steps_per_epoch=X_train.shape[0] // batch_size,
#                     validation_data=(X_val, Y_val), callbacks=callbacks, verbose=2)
# model.save('best_model.h5')
#
# # ====================模型测试====================
# np.set_printoptions(suppress=True)
# model = load_model('best_model.h5')
# res = model.predict(data[0]).reshape((data[0].shape[0], ))
# print(np.sum(res))
# res = np.where(res > 0.01, 1, 0)
# print(res)
# print(Y_test)
#
# resultPresentation(res, Y_binary)
# print()
# # descend = np.argsort(res)
# # print(max(Y_test))
# # print(Y_test[descend])


# ====================机器学习====================
# 数据预处理
nums = data[0].shape[0]
Y_binary = np.where(data[1] > 0, 1, 0)
indexes = np.arange(nums)
num_train = int(nums * 0.9)
np.random.shuffle(indexes)
train_indexes = indexes[:num_train]
test_indexes = indexes[num_train:]
X_train = data[0][train_indexes]
Y_train = Y_binary[train_indexes]
X_test = data[0][test_indexes]
Y_test = Y_binary[test_indexes]

# ====================sklearn回归====================
# model_DecisionTreeRegressor = tree.DecisionTreeRegressor()
# model_ExtraTreeRegressor = tree.ExtraTreeRegressor()
# models = [model_DecisionTreeRegressor, model_ExtraTreeRegressor]
# model_names = ['决策树回归', '极端随机树回归']
# markers = ['rx', 'go']
# # X_train = data[0][data[1] > 0]
# # Y_train = data[1][data[1] > 0]
# # X_train = data[0]
# # Y_train = data[1]
# x = np.arange(X_test.shape[0])
# fig, ax = plt.subplots(2, figsize=(15, 40))
# for i, sk in enumerate(models):
#     sk.fit(X_train, Y_train)
#     res = sk.predict(X_test)
#     print(np.sum(np.abs(res - Y_test)) / res.shape[0])
#     ax[i].plot(x, res, markers[i], label=model_names[i])
#     ax[i].plot(x, Y_test, 'b.', label='真值')
#     ax[i].legend()
#     ax[i].grid()
# plt.show()


# ====================Boosting====================
gbdt = GradientBoostingClassifier(learning_rate=0.1, n_estimators=250, max_depth=16, min_samples_leaf=30, min_samples_split=300, subsample=0.85)
gbdt.fit(X_train, Y_train)
res = gbdt.predict(X_test)
res_predprob = gbdt.predict_proba(X_test)[:, 1]
# print(res)
print(np.sum(np.abs(res - Y_test)) / res.shape[0])
print("Accuracy : %.4g" % metrics.accuracy_score(Y_test, res))
print("AUC Score: %f" % metrics.roc_auc_score(Y_test, res_predprob))
print(data[2][test_indexes][res != Y_test])
print(data[3][test_indexes][res != Y_test])
print(data[1][test_indexes][res != Y_test])

# param_test1 = {'subsample': [0.8, 0.85, 0.9, 0.95]}
# gsearch1 = GridSearchCV(estimator=GradientBoostingClassifier(learning_rate=0.1, n_estimators=250, max_depth=16, min_samples_leaf=30,
#                                                              min_samples_split=200, subsample=0.85, max_features=9, random_state=10),
#                         param_grid=param_test1, scoring='roc_auc', iid=False, cv=5)
# gsearch1.fit(X_train, Y_train)
# print(gsearch1.cv_results_)
# print(gsearch1.best_params_)
# print(gsearch1.best_score_)

# AdaBoost
# ada = AdaBoostRegressor(tree.DecisionTreeRegressor(max_depth=16), n_estimators=1000)
# ada.fit(X_train, Y_train)
# res = ada.predict(X_test)
# print(np.sum(np.abs(res - Y_test)) / res.shape[0])
# x = np.arange(X_test.shape[0])
# plt.plot(x, res, 'bx', label='AdaBoost')
# plt.plot(x, Y_test, 'r.', label='真值')
# plt.legend()
# plt.grid()
# plt.show()
