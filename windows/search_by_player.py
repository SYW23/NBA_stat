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
from util import LoadPickle
from klasses.stats_items import regular_items, playoff_items
from klasses.Player import Player


class Show_list_results(object):
    def __init__(self, res, columns):
        self.fontsize = 10
        self.col_w = 25
        self.padding = 10
        self.wd_res = Toplevel()
        self.wd_res.iconbitmap('../images/nbahalfcourt.ico')
        self.wd_res.geometry('1500x800+50+100')
        # self.wd_res.resizable(width=True, height=True)
        self.columns = columns
        self.res = res
        self.tree = None

    def title(self, tt):    # 结果窗口标题
        self.wd_res.title(tt)

    def res_note(self, text):    # 结果说明（第一行）
        Label(self.wd_res, text=text, font=('SimHei', self.fontsize), anchor='w',
              width=self.col_w, height=1).place(relx=0.015, rely=0.168, relwidth=0.2, relheight=0.022)

    def tree_generate(self):
        # 定义各列列宽及对齐方式
        for i in self.columns:
            if i in ['日期', '赛果', '上场时间']:
                self.tree.column(i, width=120, anchor='center')
            else:
                self.tree.column(i, width=100, anchor='center')
            self.tree.heading(i, text=i)
        # 逐条插入数据
        for i, r in enumerate(self.res):
            r[1] = r[1][:8]
            self.tree.insert('', i, text=str(i), values=tuple(r))
        # 滚动条
        scrollbarx = Scrollbar(self.wd_res, orient='horizontal', command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_res, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        # 布局
        scrollbarx.place(relx=0.004, rely=0.968, relwidth=0.968, relheight=0.03)
        scrollbary.place(relx=0.982, rely=0.20, relwidth=0.016, relheight=0.762)
        self.tree.place(relx=0.004, rely=0.20, relwidth=0.968, relheight=0.762)

    def loop(self, text):   # 参数：窗口标题、结果说明文字
        resbg_img = Image.open("../images/kobe_bg.jpg")
        resbg_img.putalpha(64)
        resbg_img = ImageTk.PhotoImage(resbg_img)
        Label(self.wd_res, image=resbg_img).pack()
        self.tree = ttk.Treeview(self.wd_res, columns=self.columns, show='headings')
        self.res_note(text)
        self.tree_generate()
        self.wd_res.mainloop()


class Search_by_plyr(object):
    def __init__(self):
        self.fontsize = 10
        self.col_w = 15
        self.radiobutton_w = 5
        self.paddingx = 10
        self.paddingy = 10
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
        self.v = StringVar()
        self.v.set(None)
        self.wd = Frame(self.wd_)
        self.wd.grid()
        self.wd_.bind("<Return>", self.search_enter)
        self.grid_posi = {'比赛序号': [15, 0], '日期': [15, 1], '年龄': [16, 0], '主队': [1, 0], '主客场': [1, 1],
                          '对手': [2, 0], '赛果': [2, 1], '是否首发': [3, 0], '轮次': [3, 1], '上场时间': [4, 1],
                          '命中数': [9, 0], '出手数': [9, 1], '命中率': [10, 0], '三分球命中数': [11, 0],
                          '三分球出手数': [11, 1], '三分球命中率': [12, 0], '罚球命中数': [13, 0],
                          '罚球出手数': [13, 1], '罚球命中率': [14, 0], '前场篮板': [6, 0], '后场篮板': [6, 1],
                          '篮板': [5, 0], '助攻': [5, 1], '抢断': [7, 0], '盖帽': [7, 1], '失误': [8, 0],
                          '犯规': [8, 1], '得分': [4, 0], '比赛评分': [16, 1], '正负值': [17, 0], '本轮比赛序号': [16, 0]}

    def place_stat(self, text, row, c):
        Label(self.wd, text=text + ':', font=('SimHei', self.fontsize), width=self.col_w, height=1,
              anchor='e').grid(padx=self.paddingx, pady=self.paddingy, row=row, column=c)
        if text not in ['主队', '主客场', '对手', '赛果', '是否首发', '轮次']:
            ent1 = Entry(self.wd, width=10)
            ent2 = Entry(self.wd, width=10)
            Label(self.wd, text='-', font=('SimHei', self.fontsize), width=self.col_w // 3, height=1,
                  anchor='center').grid(padx=self.paddingx//2, pady=self.paddingy, row=row, column=c + 2)
            ent1.grid(row=row, column=c + 1, padx=self.paddingx//2, pady=self.paddingy)
            ent2.grid(row=row, column=c + 3, padx=self.paddingx//2, pady=self.paddingy)
            self.stats_setting[text] = [ent1, ent2]
        else:
            ent = Entry(self.wd, width=20)
            ent.grid(row=row, column=c + 1, columnspan=3, padx=self.paddingx//2, pady=self.paddingy)
            self.stats_setting[text] = [ent]

    def ROPselection(self):
        for i in self.wd.grid_slaves()[:-7]:
            i.grid_remove()
        ROP = regular_items if self.v.get() == 'regular' else playoff_items
        self.stats_setting.clear()
        for i, k in enumerate(ROP.keys()):
            self.place_stat(k, self.grid_posi[k][0] + 2, self.grid_posi[k][1] * 4)
        self.place_stat('比赛分差', 19, 4)
        # print(self.stats_setting)

    def search_enter(self, event):    # 绑定回车键触发搜索函数
        self.search()

    def search(self):    # 点击按钮触发搜索函数
        if self.stats_setting:
            if self.plyr_ent_value.get() not in self.pn2pm.keys():
                messagebox.showinfo('提示', '球员姓名不存在！')
                return
            player = Player(self.pn2pm[self.plyr_ent_value.get()], self.v.get())
            set = {}
            for k in self.stats_setting.keys():
                ent_s = self.stats_setting[k]
                if len(ent_s) == 1:
                    if ent_s[0].get():
                        set[k] = [-1, ent_s[0].get()]    # 相等比较，-1
                else:
                    assert len(ent_s) == 2
                    if ent_s[0].get() and ent_s[1].get():    # 大于小于同时存在，2
                        set[k] = [2, [ent_s[0].get(), ent_s[1].get()]]
                    elif ent_s[0].get() and not ent_s[1].get():    # 只有大于，0
                        set[k] = [0, ent_s[0].get()]
                    elif not ent_s[0].get() and ent_s[1].get():    # 只有小于，1
                        set[k] = [1, ent_s[1].get()]
            if not set:
                messagebox.showinfo('提示', '请设置查询条件！')
            else:
                res = player.searchGame(set)
                if res:
                    RP = regular_items if self.v.get() == 'regular' else playoff_items
                    result_window = Show_list_results(res, list(RP.keys()))
                    result_window.title('%s %s 查询结果' % (self.plyr_ent_value.get(), self.ROP_dict[self.v.get()]))
                    result_window.loop(' 共查询到%d条记录' % (len(res) - 2))
                else:
                    messagebox.showinfo('提示', '未查询到符合条件的数据！')
        else:
            messagebox.showinfo('提示', '请选择比赛类型！')

    def loop(self):
        # 背景图片
        bg_img = Image.open('../images/wade&james.jpg')
        bg_img = bg_img.resize((int(bg_img.size[0] * 0.95), int(bg_img.size[1] * 0.95)))
        bg_img = cv2.cvtColor(np.asarray(bg_img), cv2.COLOR_RGB2BGR)
        bg_img = cv2.copyMakeBorder(bg_img, 0, 0, 100, 100, cv2.BORDER_REFLECT_101)
        bg_img = Image.fromarray(cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB))
        bg_img.putalpha(32)    # 透明度
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        # 控件设置
        plyr = Label(self.wd, text='球员:', font=('SimHei', self.fontsize),
                     width=self.col_w, height=1, anchor='e')
        plyr_ent = Entry(self.wd, width=20, textvariable=self.plyr_ent_value, font=('SimHei', 15))
        r1 = Radiobutton(self.wd, text='常规赛', value='regular', command=self.ROPselection,
                         variable=self.v, width=self.radiobutton_w, height=1)
        r2 = Radiobutton(self.wd, text='季后赛', value='playoff', command=self.ROPselection,
                         variable=self.v, width=self.radiobutton_w, height=1)
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=65, height=30, image=search_img,
                               compound='center', cursor='hand2', command=self.search, font=('SimHei', 14))
        notion = Label(self.wd, text='说明:', font=('SimHei', self.fontsize),
                       width=self.col_w, height=1, anchor='e')
        help_note = '主客场：0客1主\n' \
                    '比赛序号：赛季第n场比赛\n' \
                    '年龄：35-001    赛果：W/L    日期：%s\n' \
                    '季后赛轮次：E/WC1->第一轮，E/WCS->分区半决赛，\n' \
                    '            E/WCF->分区决赛，FIN->总决赛' % time.strftime("%Y%m%d")
        notion_ = Label(self.wd, text=help_note, font=('SimHei', 11),
                        width=self.col_w * 5, height=7, anchor='w', justify='left')
        # 控件布局
        plyr.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=0)
        plyr_ent.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=1, columnspan=3)
        r1.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=4)
        r2.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=4)
        search_button.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=5, columnspan=3)
        notion.grid(padx=self.paddingx, pady=self.paddingy, row=20, column=0)
        notion_.grid(padx=self.paddingx, pady=self.paddingy, row=20, rowspan=7, column=1, columnspan=7)
        # wd.attributes("-alpha", 0.8)
        self.v.set('regular')
        self.ROPselection()
        self.wd.mainloop()


if __name__ == '__main__':
    search_by_player_window = Search_by_plyr()
    search_by_player_window.loop()

