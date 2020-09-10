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
import math
import time
from multiprocessing.dummy import Pool as ThreadPool
from tqdm import tqdm
from util import LoadPickle
from klasses.stats_items import *
from klasses.Player import Player


def process(p):
    player = Player(p[0], p[1])
    min_ = 50 if p[1] == 'regular' else 5
    # print(p)
    if player.exists and player.games > min_:
        res = player.searchGame(p[2])
        if res:
            return res


class Show_single_game(object):
    def __init__(self, gm, ROP):
        self.fontsize = 10
        self.col_w = 8
        self.bt_h = 2
        self.bt_w = 10
        self.paddingx = 5
        self.paddingy = 5
        self.ROP = ROP
        self.gm = gm
        self.month = int(gm[4:6])
        self.season = int(gm[:4]) - 1 if self.month < 9 else int(gm[:4])
        game = LoadPickle('../data/seasons_boxscores/%d_%d/%s/%s_boxscores.pickle' %
                          (self.season, self.season + 1, 'playoffs' if ROP else 'regular', gm))
        [self.roadteam, self.hometeam] = [x for x in game[0].keys()]
        self.res = game[0]
        self.tbs = game[1:]
        self.columns = None
        self.wd_gm = Toplevel()
        self.wd_gm.iconbitmap('../images/nbahalfcourt.ico')
        self.wd_gm.geometry('+250+100')
        self.frame_btn = None
        self.trees = []    # 存放主客队各一个数据表格
        self.ts = 0
        self.pm2pn = LoadPickle('../data/playermark2playername.pickle')

    def button(self, text, n):
        return Button(self.frame_btn, text=text, width=self.bt_w, height=self.bt_h, compound='center',
                      cursor='hand2', command=lambda: self.span(n), font=('SimHei', self.fontsize))

    def label(self, text, fontsize):
        return Label(self.wd_gm, text=text, font=('SimHei', fontsize), width=self.col_w, height=1, anchor='center')

    def insert_tree(self, ll, tr):
        for i, r in enumerate(ll):
            tmp = r * 1
            if r[0] != 'Team Totals':
                tmp[0] = self.pm2pn[tmp[0]]
            tr.insert('', i, values=tuple(tmp)) if len(r) > 2 else tr.insert('', i, values=tuple(tmp[:1]))

    def tree_generate(self):
        self.columns = self.tbs[0][0][0]
        for ind, tr in enumerate(self.trees):
            for i in self.tbs[self.ts][ind][0]:
                tr.column(i, width=150, anchor='center') if i == 'players' else tr.column(i, width=60, anchor='center')
                tr.heading(i, text=i)
            self.insert_tree(self.tbs[self.ts][ind][1:], tr)    # 逐条插入数据
        for ind, i in enumerate(self.trees):    # 滚动条与布局
            scrollbary = Scrollbar(self.wd_gm, orient='vertical', command=i.yview)
            i.configure(yscrollcommand=scrollbary.set)
            i.grid(padx=self.paddingx, pady=self.paddingy, row=ind * 2 + 5, column=0, columnspan=5)
            scrollbary.grid(padx=self.paddingx, pady=self.paddingy, row=ind * 2 + 5, column=5, sticky='ns')

    def span(self, n):
        if self.ts != n:
            # 删除原表中数据
            for i in self.trees:
                items = i.get_children()
                [i.delete(item) for item in items]
            # 更改表头
            if n == 1 or self.ts == 1:
                for ind, tr in enumerate(self.trees):
                    for ind_c, i in enumerate(self.tbs[n][ind][0]):
                        tr.heading(self.columns[ind_c], text=i)
                    if n == 1:
                        [tr.heading(self.columns[j], text='') for j in range(ind_c + 1, len(self.columns))]    # advanced表“删除”多余的四列

            # 重新插入数据
            for ind, tr in enumerate(self.trees):
                if n > 1:    # 总计行
                    self.insert_tree(self.tbs[0][ind][-1:], tr)
                self.insert_tree(self.tbs[n][ind][1:], tr)
            self.ts = n

    def loop(self):
        gmbg_img = Image.open("../images/james.jpg")
        gmbg_img.putalpha(64)
        gmbg_img = ImageTk.PhotoImage(gmbg_img)
        Label(self.wd_gm, image=gmbg_img).place(x=0, y=0, relwidth=1, relheight=1)
        self.frame_btn = Frame(self.wd_gm)
        self.frame_btn.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=0, columnspan=5)
        # 控件设置
        rt = self.label(self.roadteam, self.fontsize * 2)
        ht = self.label(self.hometeam, self.fontsize * 2)
        rt_sr = self.label(self.res[self.roadteam][0], self.fontsize * 2)
        ht_sr = self.label(self.res[self.hometeam][0], self.fontsize * 2)
        to = self.label('vs', self.fontsize)
        rt_wl = self.label('(%s)' % self.res[self.roadteam][1], self.fontsize)
        ht_wl = self.label('(%s)' % self.res[self.hometeam][1], self.fontsize)
        btns = []    # 8个按钮
        btn_texts = ['全场', '进阶'] if self.season < 1996\
               else ['全场', '进阶', '第一节', '第二节', '上半场', '第三节', '第四节', '下半场']
        [btns.append(self.button(j, i)) for i, j in enumerate(btn_texts)]
        rt_2 = self.label(self.roadteam, self.fontsize)
        ht_2 = self.label(self.hometeam, self.fontsize)
        # 控件布局
        rt.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=0)
        rt_sr.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=1)
        to.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=2)
        ht_sr.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=3)
        ht.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=4)
        rt_wl.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=0)
        ht_wl.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=4)
        [j.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=i) for i, j in enumerate(btns)]
        rt_2.grid(padx=self.paddingx, pady=self.paddingy, row=4, column=0, sticky='w')
        ht_2.grid(padx=self.paddingx, pady=self.paddingy, row=6, column=0, sticky='w')
        self.trees = [ttk.Treeview(self.wd_gm, columns=self.tbs[0][0][0], show='headings'),
                      ttk.Treeview(self.wd_gm, columns=self.tbs[0][0][0], show='headings')]
        self.tree_generate()
        self.wd_gm.mainloop()


class Show_list_results_single(object):
    def __init__(self, res, columns, RP):
        self.fontsize = 10
        self.col_w = 25
        self.paddingx = 10
        self.paddingy = 10
        self.wd_res = Toplevel()
        self.wd_res.iconbitmap('../images/nbahalfcourt.ico')
        self.wd_res.geometry('1500x800+200+100')
        # self.wd_res.resizable(width=True, height=True)
        self.columns = columns
        self.res = res
        self.RP = 0 if RP == 'regular' else 1
        self.tree = None
        self.tree_as = None
        self.dates = [x[1] for x in res]

    def title(self, tt):  # 结果窗口标题
        self.wd_res.title(tt)

    def res_note(self, text):  # 结果说明（第一行）
        Label(self.wd_res, text=text, font=('SimHei', self.fontsize), anchor='w',
              width=self.col_w, height=1).place(relx=0.02, rely=0.15, relwidth=0.2, relheight=0.03)

    @staticmethod
    def special_sorting(l, reverse):
        if 'W' in l[0][0] or 'L' in l[0][0]:
            ast_sort = np.array([int(x[0][3:-1]) for x in l])
        elif '场' in l[0][0]:
            ast_sort = np.array([int(x[0][:-3]) for x in l])
        else:
            ast_sort = np.array([float(x[0]) if x[0] else float('nan') for x in l])
        out = np.argsort(ast_sort)
        if reverse:
            out = out[::-1]
        return [l[x] for x in out]

    def sort_column(self, col, reverse):  # 点击列名排列
        l = [[self.tree.set(k, col), k] for k in self.tree.get_children('')]  # 取出所选列中每行的值
        # print(l)
        if l[0][0].isdigit() or l[0][0] == '' or '.' in l[0][0]\
                or l[0][0][0] == '-' or l[0][0][0] == 'L' or '+' in l[0][0]\
                or '场' in l[0][0]:
            l = self.special_sorting(l, reverse)  # 特殊排序
        else:
            l.sort(reverse=reverse)  # 排序方式
        [self.tree.move(k, '', index) for index, [_, k] in enumerate(l)]  # 根据排序后的索引移动
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))  # 重写标题，使之成为再点倒序的标题

    def double(self, event):
        gm = self.dates[int(self.tree.selection()[0][1:], 16) - 1]
        game_win = Show_single_game(gm, self.RP)
        game_win.loop()

    def insert_table(self, tr, tb, command=False, _as=False):
        for i in self.columns:    # 定义各列列宽及对齐方式
            tr.column(i, width=80, anchor='center') if i in ['Date', 'WoL', 'Playoffs'] else tr.column(i, width=60, anchor='center')
            tr.heading(i, text=i) if not command else tr.heading(i, text=i, command=lambda _col=i: self.sort_column(_col, True))
        for i, r in enumerate(tb):    # 逐条插入数据
            r[1] = r[1][:8]
            ix = 8 if not self.RP else 9
            if isinstance(r[ix], str) and r[ix].count(':') == 2:
                assert r[ix][-3:] == ':00'
                r[ix] = r[ix][:-3]
            r[ix] = '0' + r[ix] if int(r[ix][:r[ix].index(':')]) < 10 else r[ix]
            for j in range(len(r)):
                if isinstance(r[j], float) and math.isnan(r[j]):
                    r[j] = ''
            tr.insert('', i, text=str(i), values=tuple(r))

    def tree_generate(self):
        self.insert_table(self.tree, self.res[:-2], command=True)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_res, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_res, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        scrollbarx.place(relx=0.005, rely=0.84, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.20, relwidth=0.015, relheight=0.65)
        self.tree.place(relx=0.005, rely=0.20, relwidth=0.97, relheight=0.65)

        self.insert_table(self.tree_as, self.res[-2:], _as=True)    # 平均&总和表
        scrollbarx_as = Scrollbar(self.wd_res, orient='horizontal', command=self.tree_as.xview)
        self.tree_as.configure(xscrollcommand=scrollbarx_as.set)
        scrollbarx_as.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)
        self.tree_as.place(relx=0.005, rely=0.87, relwidth=0.97, relheight=0.13)

    def loop(self, text):  # 参数：结果说明文字
        resbg_img = Image.open("../images/kobe_bg.jpg")
        resbg_img.putalpha(64)
        resbg_img = ImageTk.PhotoImage(resbg_img)
        Label(self.wd_res, image=resbg_img).place(x=0, y=0, relwidth=1, relheight=1)
        self.tree = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.tree_as = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.res_note(text)
        self.tree_generate()
        self.tree.bind('<Double-Button-1>', self.double)
        self.wd_res.mainloop()


class Show_list_results_group(Show_list_results_single):
    def __init__(self, res, columns, RP):
        super(Show_list_results_group, self).__init__(res, columns, RP)
        self.columns.insert(0, 'player')

    def double(self, event):
        line_number = int(self.tree.selection()[0][1:], 16) - 1
        # print(line_number)
        game_win = Show_list_results_single(self.res[line_number][1],
                                            self.columns[1:], 'regular' if self.RP == 0 else 'playoff')
        game_win.title('%s每场详细数据' % self.res[line_number][0])
        game_win.loop('')

    def insert_table(self, tr, tb):
        for i in self.columns:  # 定义各列列宽及对齐方式
            if i in ['Date', 'WoL', 'Playoffs']:
                tr.column(i, width=80, anchor='center')
            elif i == 'player':
                tr.column(i, width=150, anchor='center')
            else:
                tr.column(i, width=60, anchor='center')
            tr.heading(i, text=i, command=lambda _col=i: self.sort_column(_col, True))
        for i, r_ in enumerate(tb):  # 逐条插入数据
            r = r_[1][-2]
            r[1] = r[1][:8]
            if r[8].count(':') == 2:
                assert r[8][-3:] == ':00'
                r[8] = r[8][:-3]
            for j in range(len(r)):
                if isinstance(r[j], float) and math.isnan(r[j]):
                    r[j] = ''
            r = [r_[0]] + r
            tr.insert('', i, text=str(i), values=tuple(r))

    def tree_generate(self):
        self.insert_table(self.tree, self.res)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_res, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_res, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        scrollbarx.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.20, relwidth=0.015, relheight=0.76)
        self.tree.place(relx=0.005, rely=0.20, relwidth=0.97, relheight=0.76)


class Search_by_plyr(object):
    def __init__(self):
        self.fontsize = 10
        self.col_w = 15
        self.radiobutton_w = 5
        self.paddingx = 10
        self.paddingy = 8
        self.pm2pn = LoadPickle('../data/playermark2playername.pickle')
        self.pn2pm = dict(zip(self.pm2pn.values(), self.pm2pn.keys()))
        self.ROP_dict = {'regular': '常规赛', 'playoff': '季后赛'}
        self.wd_ = Tk()
        self.wd_.title('球员数据查询器')
        self.wd_.iconbitmap('../images/nbahalfcourt.ico')
        # wd.resizable(width=True, height=True)
        self.wd_.geometry('+500+20')
        self.stats_setting = {}
        self.plyr_ent_value = StringVar()
        self.plyr_ent_value.set('LeBron James')
        self.ROP = StringVar()
        self.ROP.set(None)
        self.PON = StringVar()
        self.PON.set('yes')
        self.wd = Frame(self.wd_)
        self.wd.grid()
        self.wd_.bind("<Return>", self.search_enter)
        self.plyr_ent = None
        self.grid_posi = {'G': [15, 0], 'Date': [15, 1], 'Age': [16, 0], 'Tm': [1, 0], 'RoH': [1, 1],
                          'Opp': [2, 0], 'WoL': [2, 1], 'GS': [3, 0], 'Series': [3, 1], 'MP': [4, 1],
                          'FG': [9, 0], 'FGA': [9, 1], 'FG%': [10, 0], '3P': [11, 0],
                          '3PA': [11, 1], '3P%': [12, 0], 'FT': [13, 0], 'Playoffs': [15, 1],
                          'FTA': [13, 1], 'FT%': [14, 0], 'ORB': [6, 0], 'DRB': [6, 1],
                          'TRB': [5, 0], 'AST': [5, 1], 'STL': [7, 0], 'BLK': [7, 1], 'TOV': [8, 0],
                          'PF': [8, 1], 'PTS': [4, 0], 'GmSc': [16, 1], '+/-': [17, 0], 'G#': [16, 0]}

    def label(self, win, text, fs, w, h, ac):
        return Label(win, text=text, font=('SimHei', fs), width=w, height=h, anchor=ac)

    def one_tick_sel(self, win, text, value, command, variable, w):
        return Radiobutton(win, text=text, value=value, command=command,
                           variable=variable, width=w, height=1)

    def place_stat(self, k, row, c):
        self.label(self.wd, en2ch[k] + ':', self.fontsize,
                   self.col_w, 1, 'e').grid(padx=self.paddingx, pady=self.paddingy, row=row, column=c)
        if k not in ['Tm', 'RoH', 'Opp', 'WoL', 'GS', 'Series']:
            ent1 = Entry(self.wd, width=10)
            ent2 = Entry(self.wd, width=10)
            self.label(self.wd, '-', self.fontsize, self.col_w // 3, 1,
                       'center').grid(padx=self.paddingx // 2, pady=self.paddingy, row=row, column=c + 2)
            ent1.grid(row=row, column=c + 1, padx=self.paddingx // 2, pady=self.paddingy)
            ent2.grid(row=row, column=c + 3, padx=self.paddingx // 2, pady=self.paddingy)
            self.stats_setting[k] = [ent1, ent2]
        else:
            ent = Entry(self.wd, width=20)
            ent.grid(row=row, column=c + 1, columnspan=3, padx=self.paddingx // 2, pady=self.paddingy)
            self.stats_setting[k] = [ent]

    def ROPselection(self):
        [i.grid_remove() for i in self.wd.grid_slaves()[:-9]]
        ROP = regular_items_en if self.ROP.get() == 'regular' else playoff_items_en
        self.stats_setting.clear()
        [self.place_stat(k, self.grid_posi[k][0] + 2, self.grid_posi[k][1] * 4) for k in ROP]
        self.place_stat('Diff', 19, 4)

    def plyr_or_not(self):    # 是否按球员分组
        self.plyr_ent['state'] = 'disabled' if self.PON.get() == 'no' else 'normal'

    def search_enter(self, event):  # 绑定回车键触发搜索函数
        self.search()

    def search(self):  # 点击按钮触发搜索函数
        if self.stats_setting:
            set = {}
            for k in self.stats_setting.keys():  # 遍历文本框控件，收集查询条件
                ent_s = self.stats_setting[k]
                if len(ent_s) == 1:
                    if ent_s[0].get():
                        set[k] = [-1, [ent_s[0].get()]]  # 相等比较，-1
                else:
                    assert len(ent_s) == 2
                    if ent_s[0].get() and ent_s[1].get():  # 大于小于同时存在，2
                        set[k] = [2, [ent_s[0].get(), ent_s[1].get()]]
                    elif ent_s[0].get() and not ent_s[1].get():  # 只有大于，0
                        set[k] = [0, [ent_s[0].get()]]
                    elif not ent_s[0].get() and ent_s[1].get():  # 只有小于，1
                        set[k] = [1, [ent_s[1].get()]]
            if not set:
                messagebox.showinfo('提示', '请设置查询条件！')
            else:
                if self.PON.get() == 'yes':    # 单球员查询
                    if self.plyr_ent_value.get() not in self.pn2pm.keys():
                        messagebox.showinfo('提示', '球员姓名不存在！')
                        return
                    player = Player(self.pn2pm[self.plyr_ent_value.get()], self.ROP.get())
                    res = player.searchGame(set)
                    # 处理结果
                    if res:
                        RP = regular_items_en if self.ROP.get() == 'regular' else playoff_items_en
                        result_window = Show_list_results_single(res, list(RP.keys()), self.ROP.get())
                        result_window.title('%s %s 查询结果' % (self.plyr_ent_value.get(), self.ROP_dict[self.ROP.get()]))
                        result_window.loop(' 共查询到%d条记录' % (len(res) - 2))
                    else:
                        messagebox.showinfo('提示', '未查询到符合条件的数据！')
                else:    # 按球员分组查询
                    # start = time.time()
                    # pp = [[x, self.ROP.get(), set] for x in list(self.pm2pn.keys())]
                    # pool = ThreadPool(4)
                    # tmp = pool.map(process, pp)
                    # pool.close()
                    # pool.join()
                    # print(len(tmp))
                    # ress = []
                    # for x in tmp:
                    #     if x:
                    #         ress.append(tmp)
                    # print(time.time() - start)
                    start = time.time()
                    res = []
                    min_ = 50 if self.ROP.get() == 'regular' else 5
                    for p in tqdm(list(self.pm2pn.keys())):
                        # print(p)
                        player = Player(p, self.ROP.get())
                        if player.exists and not isinstance(player.data, list) and player.games > min_:
                            tmp = player.searchGame(set)
                            if tmp:
                                res.append([self.pm2pn[p], tmp])
                    # print(len(ress))
                    print(time.time() - start)
                    if res:
                        RP = regular_items_en if self.ROP.get() == 'regular' else playoff_items_en
                        result_window = Show_list_results_group(res, list(RP.keys()), self.ROP.get())
                        result_window.title('%s查询结果' % ('常规赛' if self.ROP.get() == 'regular' else '季后赛'))
                        result_window.loop(' 共查询到%d个球员' % len(res))
                    else:
                        messagebox.showinfo('提示', '未查询到符合条件的数据！')
                    return
        else:
            messagebox.showinfo('提示', '请选择比赛类型！')

    def loop(self):
        # 背景图片
        bg_img = Image.open('../images/wade&james.jpg')
        bg_img = bg_img.resize((int(bg_img.size[0] * 0.95), int(bg_img.size[1] * 0.95)))
        bg_img = cv2.cvtColor(np.asarray(bg_img), cv2.COLOR_RGB2BGR)
        bg_img = cv2.copyMakeBorder(bg_img, 0, 0, 100, 100, cv2.BORDER_REFLECT_101)
        bg_img = Image.fromarray(cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB))
        bg_img.putalpha(32)  # 透明度
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        # 控件设置
        plyr_fm = Frame(self.wd, height=1)
        plyr_yes = self.one_tick_sel(plyr_fm, '单球员查询', 'yes', self.plyr_or_not, self.PON, self.radiobutton_w * 2)
        plyr_no = self.one_tick_sel(plyr_fm, '按球员分组', 'no', self.plyr_or_not, self.PON, self.radiobutton_w * 2)
        plyr = self.label(self.wd, '球员:', self.fontsize, self.col_w, 1, 'e')
        self.plyr_ent = Entry(self.wd, width=20, textvariable=self.plyr_ent_value, font=('SimHei', 15))
        rglr_sel = self.one_tick_sel(self.wd, '常规赛', 'regular', self.ROPselection, self.ROP, self.radiobutton_w)
        plyf_sel = self.one_tick_sel(self.wd, '季后赛', 'playoff', self.ROPselection, self.ROP, self.radiobutton_w)
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=65, height=30, image=search_img,
                               compound='center', cursor='hand2', command=self.search, font=('SimHei', 14))
        sep = ttk.Separator(self.wd, orient='horizontal')  # 分割线
        notion = self.label(self.wd, '说明:', self.fontsize, self.col_w, 1, 'e')
        help_note = '主客场：0客1主\n比赛序号：赛季第n场比赛\n' \
                    '年龄：35-001    赛果：W/L    日期：%s\n' \
                    '季后赛轮次：E/WC1->第一轮，E/WCS->分区半决赛，\n' \
                    '            E/WCF->分区决赛，FIN->总决赛' % time.strftime("%Y%m%d")
        notion_ = Label(self.wd, text=help_note, font=('SimHei', 11),
                        width=self.col_w * 5, height=6, anchor='w', justify='left')
        # 控件布局
        plyr_fm.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=0, columnspan=4)
        plyr_yes.grid(row=1, column=0)
        plyr_no.grid(row=1, column=1)
        plyr.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=0)
        self.plyr_ent.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=1, columnspan=3)
        rglr_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=4)
        plyf_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=4)
        search_button.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=5, columnspan=3)
        sep.grid(row=20, column=0, columnspan=8, sticky='ew')
        notion.grid(padx=self.paddingx, pady=self.paddingy, row=26, column=0)
        notion_.grid(padx=self.paddingx, pady=self.paddingy, row=26, rowspan=6, column=1, columnspan=7)
        # wd.attributes("-alpha", 0.8)
        # self.ROP.set('regular')
        # self.ROPselection()
        self.wd.mainloop()


if __name__ == '__main__':
    search_by_player_window = Search_by_plyr()
    search_by_player_window.loop()
