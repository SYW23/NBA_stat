#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from util import LoadPickle
from klasses.stats_items import *
from klasses.Player import Player
from result_windows import ShowSingleGame, ShowResults, ShowSingleResults, ShowGroupResults

cmps = {-1: ['=='], 0: ['>='], 1: ['<='], 2: ['>=', '<=']}


class searchByPlyr(object):
    def __init__(self):
        self.fontsize = 10
        self.col_w = 15
        self.radiobutton_w = 5
        self.paddingx = 10
        self.paddingy = 8
        self.pm2pn = LoadPickle('../data/playermark2playername.pickle')
        self.pn2pm = dict(zip(self.pm2pn.values(), self.pm2pn.keys()))
        self.RoP_dict = {'regular': '常规赛', 'playoff': '季后赛'}
        self.wd_ = Tk()
        self.wd_.title('球员数据查询器')
        self.wd_.iconbitmap('../images/nbahalfcourt.ico')
        # wd.resizable(width=True, height=True)
        self.wd_.geometry('+500+20')
        self.stats_setting = {}    # 保存查询条件设置
        self.plyr_ent_value = StringVar()
        self.plyr_ent_value.set('LeBron James')
        self.RoP = StringVar()
        self.RoP.set(None)
        self.AoS = StringVar()
        self.AoS.set(None)
        self.scope = StringVar()
        self.PON = StringVar()
        self.PON.set('yes')
        self.wd = Frame(self.wd_)
        self.wd.grid()
        self.wd_.bind("<Return>", self.search_enter)
        self.plyr = None
        self.plyr_ent = None

    def label(self, win, text, fs, w, h, ac):
        return Label(win, text=text, font=('SimHei', fs), width=w, height=h, anchor=ac)

    def one_tick_sel(self, win, text, value, w, variable, command):
        return Radiobutton(win, text=text, value=value, command=command,
                           variable=variable, width=w, height=1)

    def place_sep(self, win, row, columnspan=12):    # 分割线
        sep = ttk.Separator(win, orient='horizontal')
        sep.grid(padx=3, pady=3, row=row, column=0, columnspan=columnspan, sticky='ew')

    def place_equal_inf(self, row):    # 信息数据Frame
        equal_fm = Frame(self.wd)
        equal_fm.grid(row=row, column=0, columnspan=12)
        ls = ['Tm', 'Opp', 'GS', 'RoH', 'WoL'] if self.RoP.get() == 'regular'\
            else ['Tm', 'Opp', 'GS', 'RoH', 'WoL', 'Series']
        self.place_stat(equal_fm, ls, 'i // 3 + 1', 'i % 3 * 2', type=0)

    def place_basic(self, row):    # 基础数据Frame
        basic_fm = Frame(self.wd)
        basic_fm.grid(row=row, column=0, columnspan=12)
        ls = ['PTS', 'TRB', 'AST', 'BLK', 'STL', 'TOV', 'ORB', 'DRB', 'PF', 'MP', 'GmSc', '+/-']
        self.place_stat(basic_fm, ls, 'i // 3 + 1', 'i % 3 * 4')

    def place_shooting(self, row):    # 投篮数据Frame
        shooting_fm = Frame(self.wd)
        shooting_fm.grid(row=row, column=0, columnspan=12)
        ls = ['FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%']
        self.place_stat(shooting_fm, ls, 'i // 3 + 1', 'i % 3 * 4')

    def place_inf(self, row):    # 信息比较数据Frame
        inf_fm = Frame(self.wd)
        inf_fm.grid(row=row, column=0, columnspan=12)
        ls = ['G', 'Date', 'Age', 'Diff'] if self.RoP.get() == 'regular'\
            else ['G', 'Playoffs', 'G#', 'Diff']
        self.place_stat(inf_fm, ls, 'i // 2 + 1', 'i % 2 * 4')

    def place_stat(self, win, ls, row_, col_, type=1):    # type 1:大于小于 0:等于
        # ==============查询条件输入框布局====================
        for i, k in enumerate(ls):
            row, col = eval(row_), eval(col_)
            if type:
                self.label(win, en2ch[k][0] + ':', self.fontsize,
                           self.col_w, 1, 'e').grid(padx=self.paddingx, pady=self.paddingy, row=row, column=col)
                ent1, ent2 = Entry(win, width=10), Entry(win, width=10)
                self.label(win, '-', self.fontsize, self.col_w // 3, 1,
                           'center').grid(padx=self.paddingx // 2, pady=self.paddingy, row=row, column=col + 2)
                ent1.grid(row=row, column=col + 1, padx=self.paddingx // 2, pady=self.paddingy)
                ent2.grid(row=row, column=col + 3, padx=self.paddingx // 2, pady=self.paddingy)
                self.stats_setting[k] = [ent1, ent2]
            else:
                self.label(win, en2ch[k][0] + ':', self.fontsize,
                           12, 1, 'center').grid(padx=self.paddingx, pady=self.paddingy, row=row, column=col)
                ent = Entry(win, width=10)
                ent.grid(row=row, column=col + 1, padx=self.paddingx, pady=self.paddingy)
            self.stats_setting[k] = eval('[ent1, ent2]') if type else eval('[ent]')

    def RoPselection(self):
        [i.grid_remove() for i in self.wd.grid_slaves()[:-10]]
        self.place_equal_inf(3)
        self.place_sep(self.wd, 4)
        self.place_basic(5)
        self.place_sep(self.wd, 6)
        self.place_shooting(7)
        self.place_sep(self.wd, 8)
        self.place_inf(9)

    def AoSselection(self):
        pass

    def plyr_or_not(self):    # 是否按球员分组
        self.plyr['text'] = '最小场数' if self.PON.get() == 'no' else '球员'
        self.plyr_ent_value.set('1') if self.PON.get() == 'no' else self.plyr_ent_value.set('LeBron James')

    def search_enter(self, event):  # 绑定回车键触发搜索函数
        self.search()

    def search(self):  # 点击按钮触发搜索函数
        if self.stats_setting:
            stats = {}
            for k in self.stats_setting.keys():  # 遍历文本框控件，收集查询条件
                tp = 1 if en2ch[k][1] == 1 or k == 'WoL' or k == 'MP' else 0
                ent_s = self.stats_setting[k]
                if len(ent_s) == 1:    # 相等比较
                    if ent_s[0].get():
                        stats[k] = [' == "%s" and ' % ent_s[0].get() if tp else ' == %s and ' % ent_s[0].get()]
                else:
                    if ent_s[0].get() and ent_s[1].get():  # 大于小于同时存在
                        stats[k] = [' >= "%s" and ' % ent_s[0].get() if tp else ' >= %s and ' % ent_s[0].get(),
                                    ' <= "%s" and ' % ent_s[1].get() if tp else ' <= %s and ' % ent_s[1].get()]
                    elif ent_s[0].get() and not ent_s[1].get():  # 只有大于
                        stats[k] = [' >= "%s" and ' % ent_s[0].get() if tp else ' >= %s and ' % ent_s[0].get()]
                    elif not ent_s[0].get() and ent_s[1].get():  # 只有小于
                        stats[k] = [' <= "%s" and ' % ent_s[1].get() if tp else ' <= %s and ' % ent_s[1].get()]
            if not stats:
                messagebox.showinfo('提示', '请设置查询条件！')
            else:
                if self.PON.get() == 'yes':  # 单球员查询
                    if self.plyr_ent_value.get() not in self.pn2pm.keys():
                        messagebox.showinfo('提示', '球员姓名不存在！')
                        return
                    player = Player(self.pn2pm[self.plyr_ent_value.get()], self.RoP.get())
                    if self.scope.get() == '单场比赛':
                        pt = 1
                        res = player.search_by_game(stats)
                    elif self.scope.get() == '赛季':
                        pt = 2
                        res = player.search_by_season(stats, int(self.AoS.get()))
                    elif self.scope.get() == '职业生涯':
                        pt = 2
                        res = player.search_by_career(stats, int(self.AoS.get()))
                        res = [[self.plyr_ent_value.get(), x] for x in res]
                    elif self.scope.get() == '连续比赛':
                        pt = 0
                        res = player.search_by_consecutive(stats)
                else:    # 按球员分组查询
                    pt = 0
                    # start = time.time()
                    # pp = [[x, self.RoP.get(), stats] for x in list(self.pm2pn.keys())]
                    # print(time.time() - start)
                    # pool = ThreadPool(4)
                    # tmp = pool.map(process, pp)
                    # pool.close()
                    # pool.join()
                    # print(time.time() - start)
                    # res = []
                    # for x in tmp:
                    #     if x:
                    #         res.append(x)
                    # print(time.time() - start)
                    start = time.time()
                    res = []
                    min_ = 50 if self.RoP.get() == 'regular' else 5
                    for p in tqdm(list(self.pm2pn.keys())):
                        player = Player(p, self.RoP.get())
                        if player.exists and not isinstance(player.data, list) and player.games > min_:
                            if self.scope.get() == '单场比赛':
                                tmp = player.search_by_game(stats, minG=int(self.plyr_ent_value.get()))
                                if tmp:
                                    res.append([self.pm2pn[p], tmp])
                            elif self.scope.get() == '赛季':
                                pt = 2
                                tmp = player.search_by_season(stats, int(self.AoS.get()))
                                res += tmp
                            elif self.scope.get() == '职业生涯':
                                pt = 2
                                tmp = player.search_by_career(stats, int(self.AoS.get()))
                                if tmp:
                                    tmp = [[self.pm2pn[p], x] for x in tmp]
                                    res += tmp
                            elif self.scope.get() == '连续比赛':
                                pt = 0
                                res += player.search_by_consecutive(stats, minG=int(self.plyr_ent_value.get()))
                    print(time.time() - start)
                # 处理结果
                if res:
                    RP = regular_items_en if self.RoP.get() == 'regular' else playoff_items_en
                    win_klass = ShowSingleResults if pt else ShowGroupResults
                    # print(win_klass)
                    if pt == 2:
                        win_klass = ShowResults
                    result_window = win_klass(res, list(RP.keys()), self.RoP.get(), detail=False if pt else True)
                    win_title = '%s %s 查询结果（按%s）' % (self.plyr_ent_value.get(),
                                                     self.RoP_dict[self.RoP.get()], self.scope.get())\
                        if pt else '%s查询结果（按%s）' % ('常规赛' if self.RoP.get() == 'regular' else '季后赛', self.scope.get())
                    result_window.title(win_title)
                    num = (len(res) - 2 * pt) if pt != 2 else len(res)
                    result_window.loop('共查询到%d组数据' % num, stats)
                else:
                    messagebox.showinfo('提示', '未查询到符合条件的数据！')
        else:
            messagebox.showinfo('提示', '请选择比赛类型！')

    def loop(self):
        # ==============背景图片====================
        bg_img = Image.open('../images/james.jpg')
        bg_img = bg_img.resize((int(bg_img.size[0] * 0.95), int(bg_img.size[1] * 0.95)))
        bg_img = cv2.cvtColor(np.asarray(bg_img), cv2.COLOR_RGB2BGR)
        bg_img = cv2.copyMakeBorder(bg_img, 0, 0, 100, 100, cv2.BORDER_REFLECT_101)
        bg_img = Image.fromarray(cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB))
        bg_img.putalpha(32)  # 透明度
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        # ==============球员名称label&entry====================
        self.plyr = self.label(self.wd, '球员:', self.fontsize, self.col_w, 1, 'e')
        self.plyr_ent = Entry(self.wd, width=20, textvariable=self.plyr_ent_value, font=('SimHei', 15))
        self.plyr.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=0)
        self.plyr_ent.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=1, columnspan=3)
        # ==============单球员or多球员单选Frame====================
        plyr_fm = Frame(self.wd, height=1)
        plyr_yes = self.one_tick_sel(plyr_fm, '单球员查询', 'yes', self.radiobutton_w * 2, self.PON, self.plyr_or_not)
        plyr_no = self.one_tick_sel(plyr_fm, '按球员分组', 'no', self.radiobutton_w * 2, self.PON, self.plyr_or_not)
        plyr_fm.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=4, columnspan=3)
        plyr_yes.grid(row=1, column=0)
        plyr_no.grid(row=1, column=1)
        # ==============比赛类型组合选择Frame====================
        gametype_fm = Frame(self.wd)
        rglr_sel = self.one_tick_sel(gametype_fm, '常规赛', 'regular', self.radiobutton_w, self.RoP, self.RoPselection)
        plyf_sel = self.one_tick_sel(gametype_fm, '季后赛', 'playoff', self.radiobutton_w, self.RoP, self.RoPselection)
        scope_sel = ttk.Combobox(gametype_fm, width=7, textvariable=self.scope)
        scope_sel['value'] = ['单场比赛', '赛季', '职业生涯', '连续比赛', '连续赛季']
        scope_sel.current(0)
        ave_sel = self.one_tick_sel(gametype_fm, '场均', '1', 2, self.AoS, self.AoSselection)
        sum_sel = self.one_tick_sel(gametype_fm, '总和', '0', 2, self.AoS, self.AoSselection)
        self.AoS.set('1')
        self.place_sep(gametype_fm, 2, columnspan=2)
        gametype_fm.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=7, columnspan=4)
        rglr_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=0)
        plyf_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=1)
        scope_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=3, column=2, columnspan=2)
        ave_sel.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=0, sticky='e')
        sum_sel.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=1, sticky='w')
        # ==============搜索button====================
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=60, height=30, image=search_img,
                               compound='center', cursor='hand2', command=self.search, font=('SimHei', 14))
        search_button.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=11)
        # ==============说明label====================
        self.place_sep(self.wd, 20)
        notion = self.label(self.wd, '说明:', self.fontsize, self.col_w, 1, 'e')
        help_note = '主客场：0客1主    比赛序号：赛季第n场比赛\n' \
                    '年龄：35-001    赛果：W/L    日期：%s\n' \
                    '季后赛轮次：E/WC1->第一轮，E/WCS->分区半决赛，' \
                    'E/WCF->分区决赛，FIN->总决赛' % time.strftime("%Y%m%d")
        notion_ = Label(self.wd, text=help_note, font=('SimHei', 11),
                        width=self.col_w * 5, height=6, anchor='w', justify='left')
        notion.grid(padx=self.paddingx, pady=self.paddingy, row=26, column=0)
        notion_.grid(padx=self.paddingx, pady=self.paddingy, row=26, rowspan=6, column=1, columnspan=11, sticky='w')
        # wd.attributes("-alpha", 0.8)
        self.RoP.set('regular')
        self.RoPselection()
        self.wd.mainloop()


if __name__ == '__main__':
    search_by_player_window = searchByPlyr()
    search_by_player_window.loop()
