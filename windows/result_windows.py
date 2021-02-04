#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import math
from util import LoadPickle
from klasses.stats_items import *
from klasses.Player import Player


def process(p):
    player = Player(p[0], p[1])
    min_ = 50 if p[1] == 'regular' else 5
    if player.exists and not isinstance(player.data, list) and player.games > min_:
        res = player.search_by_game(p[2])
        if res:
            return res


class ShowSingleGame(object):
    def __init__(self, gm, RoP):
        self.fontsize = 10
        self.col_w = 8
        self.bt_h = 2
        self.bt_w = 10
        self.paddingx = 5
        self.paddingy = 5
        self.RoP = RoP if isinstance(RoP, int) else (1 if 'playoff' in RoP else 0)
        self.gm = gm[:-7] if '.pickle' in gm else gm
        self.month = int(gm[4:6])
        self.season = int(gm[:4]) - 1 if self.month < 9 else int(gm[:4])
        game = LoadPickle('D:/sunyiwu/stat/data/seasons_boxscores/%d_%d/%s/%s_boxscores.pickle' %
                          (self.season, self.season + 1, 'playoff' if self.RoP else 'regular', self.gm))
        [self.roadteam, self.hometeam] = [x for x in game[0].keys()]
        self.res = game[0]
        self.tbs = game[1:]
        self.columns = None
        self.wd_gm = Toplevel()
        self.wd_gm.iconbitmap('D:/sunyiwu/stat/images/nbahalfcourt.ico')
        self.wd_gm.geometry('+250+100')
        self.frame_btn = None
        self.trees = []    # 存放主客队各一个数据表格
        self.ts = 0
        self.pm2pn = LoadPickle('D:/sunyiwu/stat/data/playermark2playername.pickle')

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
        gmbg_img = Image.open("D:/sunyiwu/stat/images/james.jpg")
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


class ShowTables(object):
    def __init__(self, tb, columns, top=True):
        self.tb = tb
        self.columns = columns
        if top:
            self.wd_tb = Tk()
        else:
            self.wd_tb = Toplevel()
        self.wd_tb.geometry('1000x800+100+100')
        self.tree = None

    @staticmethod
    def special_sorting(l, reverse):  # 考虑排序各种情况
        ast_sort = np.array([float(x[0]) for x in l])
        out = np.argsort(ast_sort)
        if reverse:
            out = out[::-1]
        return [l[x] for x in out]

    def sort_column(self, col, reverse):  # 点击列名排列
        l = [[self.tree.set(k, col), k] for k in self.tree.get_children('')]  # 取出所选列中每行的值
        try:
            tmp = float(l[0][0])
            l = self.special_sorting(l, reverse)
        except:
            l.sort(reverse=reverse)  # 排序方式
        [self.tree.move(k, '', index) for index, [_, k] in enumerate(l)]  # 根据排序后的索引移动
        self.tree.heading(col, command=lambda: self.sort_column(col, 0 if reverse else 1))

    def insert_table(self, tr, tb):
        for i in self.columns:  # 定义各列列宽及对齐方式
            tr.column(i, width=100, anchor='center')
            tr.heading(i, text=i, command=lambda _col=i: self.sort_column(_col, 1))
        for i, r in enumerate(tb):    # 逐条插入数据
            tr.insert('', i, text=str(i), values=tuple(r))

    def tree_generate(self):
        self.insert_table(self.tree, self.tb)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_tb, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_tb, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        scrollbarx.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.20, relwidth=0.02, relheight=0.76)
        self.tree.place(relx=0.005, rely=0.20, relwidth=0.97, relheight=0.76)

    def loop(self, text):  # 参数：结果说明文字
        self.wd_tb.title(text)
        self.tree = ttk.Treeview(self.wd_tb, columns=self.columns, show='headings')
        self.tree_generate()
        self.wd_tb.mainloop()


class ShowResults(object):
    def __init__(self, res, columns, RP, detail=True):
        self.fontsize = 10
        self.font = ('SimHei', self.fontsize)
        self.col_w = 25
        self.paddingx = 10
        self.paddingy = 10
        self.wd_res = Toplevel()
        self.wd_res.iconbitmap('D:/sunyiwu/stat/images/nbahalfcourt.ico')
        self.wd_res.geometry('1920x800+0+100')
        # self.wd_res.resizable(width=True, height=True)
        self.columns = columns
        self.res = res
        self.RP = 0 if RP == 'regular' else 1
        self.tree = None
        self.dates = [x[1] for x in res]
        # print(self.dates)
        self.stats = None
        self.cmps = {-1: ['=='], 0: ['>='], 1: ['<=']}
        self.p = 0    # 是否有Player列
        if len(self.res[0]) == 2:
            self.columns.insert(0, 'Player')
            self.p = 1
        self.widths = {'G': 80, 'Date': 80, 'Age': 60, 'Tm': 60, 'RoH': 80 if self.p else 60, 'Opp': 60,
                       'WoL': 100 if self.p else 80, 'GS': 80 if self.p else 60, 'MP': 60,
                       'FG': 60, 'FGA': 60, 'FG%': 60, '3P': 60, '3PA': 60, '3P%': 60, 'FT': 60, 'FTA': 60, 'FT%': 60,
                       'ORB': 60, 'DRB': 60, 'TRB': 60, 'AST': 60, 'STL': 60, 'BLK': 60, 'TOV': 60, 'PF': 60, 'PTS': 60,
                       'GmSc': 60, '+/-': 60, 'Playoffs': 80, 'Series': 60, 'G#': 60, 'Player': 180}

    def title(self, tt):  # 结果窗口标题
        self.wd_res.title(tt)

    def res_note(self, text):  # 结果说明（第一行）
        Label(self.wd_res, text=text, font=self.font, anchor='w', width=self.col_w, height=1).place(relx=0.02, rely=0.15, relwidth=0.2, relheight=0.03)

    def settings_note(self, stats):  # 查询条件展示
        self.stats = stats
        text = '查询条件：'
        for k in stats:
            ch, tp = en2ch[k][0], len(stats[k])
            tmp = '%s%s  ' % (ch, stats[k][0][:-5]) if tp < 2\
                else '%s %s %s %s %s  ' % (stats[k][0][4:-5], '<=', ch, '<=', stats[k][1][4:-5])
            text += tmp
        Label(self.wd_res, text=text, font=self.font, anchor='w', width=self.col_w, height=1).place(relx=0.221, rely=0.15, relwidth=0.42, relheight=0.03)

    @staticmethod
    def special_sorting(l, reverse):    # 考虑排序各种情况
        n, tp = 0, 0
        if ('W' in l[0][0] or 'L' in l[0][0]) and '(' in l[0][0] and '.' not in l[0][0]:    # WoL
            ast_sort = np.array([int(x[0][3:-1]) for x in l])
        elif '场' in l[0][0]:    # group G
            ast_sort = np.array([int(x[0][:-3]) for x in l])
        elif 'R/' in l[0][0]:    # group RoH
            tp = 1
            dt = np.dtype([('R', np.float64), ('H', np.float64)])
            ast_sort = np.array([(int(x[0][:x[0].index('R')]), int(x[0][x[0].index('/') + 1:-1])) for x in l], dtype=dt)
        elif '/' in l[0][0] and '(' in l[0][0] and ')' in l[0][0]:    # group WoL
            tp = 1
            dt = np.dtype([('P', np.float64), ('G', np.float64), ('D', np.float64)])
            ast_sort = np.array(
                [(int(x[0][:x[0].index('W')]) / (int(x[0][:x[0].index('W')]) +
                                                 int(x[0][x[0].index('/') + 1:x[0].index('L')])),
                  int(x[0][:x[0].index('W')]) + int(x[0][x[0].index('/') + 1:x[0].index('L')]),
                  float(x[0][x[0].index('(')+1:-1])) for x in l], dtype=dt)
        else:
            for i in l:
                if '@' in i[0] or ':' in i[0]:    # RoH or MP
                    tp = 1
                    break
                elif '/' in i[0]:
                    tp = 2
                    break
            if tp == 0:
                ast_sort = np.array([float(x[0]) if x[0] else float('nan') for x in l])
                for i in ast_sort:
                    if i == '' or math.isnan(i):
                        n += 1
            elif tp == 1:
                ast_sort = np.array([i[0] for i in l])
                for i in ast_sort:
                    if i == '':
                        n += 1
            else:
                dt = np.dtype([('S', np.float64), ('G', np.float64)])
                ast_sort = np.array([(int(x[0][:x[0].index('/')]) / int(x[0][x[0].index('/') + 1:]),
                                      int(x[0][x[0].index('/') + 1:])) if x[0] else float('nan') for x in l], dtype=dt)
                for i in ast_sort:
                    if isinstance(i[0], float) and math.isnan(i[0]):
                        n += 1
        out = list(np.argsort(ast_sort))
        if reverse:
            out = out[::-1]
            out = out[n:] + out[:n] if tp != 1 else out
        else:
            if tp == 1:
                out = out[n:] + out[:n]
        return [l[x] for x in out]

    def sort_column(self, col, reverse):  # 点击列名排列
        l = [[self.tree.set(k, col), k] for k in self.tree.get_children('')]  # 取出所选列中每行的值
        # print(l)
        if l[0][0].isdigit() or l[0][0] == '' or '.' in l[0][0] \
                or l[0][0][0] == '-' or l[0][0][0] == 'L' or '+' in l[0][0] \
                or '场' in l[0][0] or '@' in l[0][0] or ':' in l[0][0] or 'r/' in l[0][0] \
                or ('/' in l[0][0] and l[0][0] != '/'):
            l = self.special_sorting(l, reverse)  # 特殊排序
        else:
            l.sort(reverse=reverse)  # 排序方式
        [self.tree.move(k, '', index) for index, [_, k] in enumerate(l)]  # 根据排序后的索引移动
        self.tree.heading(col, command=lambda: self.sort_column(col, 0 if reverse else 1))

    def set_tc(self, tr, command=False):
        for i in self.columns:    # 定义各列列宽及对齐方式
            tr.column(i, width=self.widths[i], anchor='center')
            tr.heading(i, text=i, command=lambda _col=i: self.sort_column(_col, 1)) if command else tr.heading(i, text=i)

    def deal_with_tr(self, r):
        r[1] = r[1][:8]
        ix = 8 if not self.RP else 9
        if isinstance(r[ix], str) and r[ix].count(':') == 2:
            assert r[ix][-3:] == ':00'
            r[ix] = r[ix][:-3]
        if isinstance(r[ix], str) and r[ix] and int(r[ix][:r[ix].index(':')]) < 10:
            r[ix] = '0' + r[ix]
        for j in range(len(r)):
            if (isinstance(r[j], float) and math.isnan(r[j])) or r[j] == 'nan':
                r[j] = ''

    def insert_table(self, tr, tb, command=False):
        self.set_tc(tr, command=command)
        for i, r in enumerate(tb):    # 逐条插入数据
            if self.p:
                r = r[1]
            self.deal_with_tr(r)
            tr.insert('', i, text=str(i), values=tuple([tb[i][0]] + r if self.p else r))

    def tree_generate(self):
        self.insert_table(self.tree, self.res, command=True if self.p else False)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_res, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_res, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        scrollbarx.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.20, relwidth=0.015, relheight=0.76)
        self.tree.place(relx=0.005, rely=0.20, relwidth=0.97, relheight=0.76)

    def bkgdimg_and_note(self, text, stats):
        resbg_img = Image.open("D:/sunyiwu/stat/images/kobe_bg.jpg")
        resbg_img.putalpha(64)
        resbg_img = ImageTk.PhotoImage(resbg_img)
        Label(self.wd_res, image=resbg_img).place(x=0, y=0, relwidth=1, relheight=1)
        self.res_note(text)
        self.settings_note(stats)

    def loop(self, text, stats):  # 参数：结果说明文字
        self.bkgdimg_and_note(text, stats)
        self.tree = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.tree_generate()
        self.wd_res.mainloop()


class ShowSingleResults(ShowResults):
    def __init__(self, res, columns, RP, detail=True, AoS=None):
        super(ShowSingleResults, self).__init__(res, columns, RP)
        self.tree_as = None

    def double(self, event):
        gm = self.dates[int(self.tree.selection()[0][1:], 16) - 1]
        game_win = ShowSingleGame(gm, self.RP)
        game_win.loop()

    def tree_generate(self):
        self.insert_table(self.tree, self.res[:-2], command=True)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_res, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_res, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        scrollbarx.place(relx=0.005, rely=0.84, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.20, relwidth=0.015, relheight=0.65)
        self.tree.place(relx=0.005, rely=0.20, relwidth=0.97, relheight=0.65)

        self.insert_table(self.tree_as, self.res[-2:])    # 平均&总和表
        scrollbarx_as = Scrollbar(self.wd_res, orient='horizontal', command=self.tree_as.xview)
        self.tree_as.configure(xscrollcommand=scrollbarx_as.set)
        scrollbarx_as.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)
        self.tree_as.place(relx=0.005, rely=0.87, relwidth=0.97, relheight=0.13)

    def loop(self, text, stats):  # 参数：结果说明文字
        self.bkgdimg_and_note(text, stats)
        self.tree = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.tree_as = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.tree_generate()
        self.tree.bind('<Double-Button-1>', self.double)
        self.wd_res.mainloop()


class ShowGroupResults(ShowResults):
    def __init__(self, res, columns, RP, detail=True, AoS=1):
        super(ShowGroupResults, self).__init__(res, columns, RP)
        # self.columns.insert(0, 'Player')
        self.detail = detail
        self.AoS = AoS
        self.dates = [[j[1] for j in i[1][:-2]] for i in self.res]

    def double(self, event):
        line_number = int(self.tree.selection()[0][1:], 16) - 1
        game_win = ShowSingleResults(self.res[line_number][1], self.columns[1:], 'playoff' if self.RP else 'regular')
        game_win.dates = self.dates[line_number]
        game_win.title('%s每场详细数据' % self.res[line_number][0])
        game_win.loop('共查询到%d条记录' % (len(self.res[line_number][1]) - 2), self.stats)

    def insert_table(self, tr, tb, command=False):
        self.set_tc(tr, command=True)
        for i, r_ in enumerate(tb):  # 逐条插入数据
            r = r_[1][-2 if self.AoS else -1] if self.detail else r_[1]
            self.deal_with_tr(r)
            r = [r_[0]] + r
            tr.insert('', i, text=str(i), values=tuple(r))

    def loop(self, text, stats):  # 参数：结果说明文字
        self.bkgdimg_and_note(text, stats)
        self.tree = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.tree_generate()
        self.tree.bind('<Double-Button-1>', self.double)
        self.wd_res.mainloop()

