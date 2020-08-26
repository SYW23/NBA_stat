#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from util import LoadPickle
from klasses.stats_items import regular_items, playoff_items
from klasses.Player import Player


class show_list_results(object):
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
            if i == '日期':
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
        self.padding = 10
        self.pm2pn = LoadPickle('../data/playermark2playername.pickle')
        self.pn2pm = dict(zip(self.pm2pn.values(), self.pm2pn.keys()))
        self.ROP_dict = {'regular': '常规赛', 'playoff': '季后赛'}
        self.wd = Tk()
        self.wd.title('数据查询器')
        self.wd.iconbitmap('../images/nbahalfcourt.ico')
        # wd.resizable(width=True, height=True)
        self.wd.geometry('+500+20')
        self.comboboxs = []
        self.stats = []
        self.plyr_ent_value = StringVar()
        self.plyr_ent_value.set('LeBron James')
        self.v = StringVar()
        self.v.set(None)
        self.wd.bind("<Return>", self.search_enter)

    def place_stat(self, text, row, c):
        Label(self.wd, text=text + ':', font=('SimHei', self.fontsize), width=self.col_w, height=1,
              anchor='e').grid(padx=self.padding, pady=self.padding, row=row, column=c)
        gol = StringVar()
        gl = ttk.Combobox(self.wd, width=5, textvariable=gol)
        if text not in ['主队', '主客场', '对手', '赛果', '是否首发', '轮次']:
            gl['value'] = ['    >=', '    <=']
        else:
            gl['value'] = ['    ==']
        gl.current(0)
        ent = Entry(self.wd, width=10)

        self.comboboxs.append(gol)
        self.stats.append(ent)

        gl.grid(row=row, column=c+1, padx=self.padding, pady=self.padding)
        ent.grid(row=row, column=c+2, padx=self.padding, pady=self.padding)

    def selection(self):
        if len(self.stats) == 30:
            for i in range(3):
                self.wd.grid_slaves()[0].grid_remove()
        ROP = regular_items if self.v.get() == 'regular' else playoff_items
        self.comboboxs.clear()
        self.stats.clear()
        for i, k in enumerate(ROP.keys()):
            if i % 2 == 0:
                self.place_stat(k, i//2 + 2, 0)
            else:
                self.place_stat(k, i//2 + 2, 3)
        if i == 28:
            self.place_stat('分差', i//2 + 2, 3)
        else:
            self.place_stat('分差', i//2 + 3, 0)

    def search_enter(self, event):    # 绑定回车键触发搜索函数
        self.search()

    def search(self):    # 点击按钮触发搜索函数
        if self.stats:
            if self.plyr_ent_value.get() not in self.pn2pm.keys():
                messagebox.showinfo('提示', '球员姓名不存在！')
                return
            player = Player(self.pn2pm[self.plyr_ent_value.get()], self.v.get())
            res = player.searchGame(self.comboboxs, self.stats)
            if res == [-1]:
                messagebox.showinfo('提示', '请设置查询条件！')
            else:
                if res:
                    RP = regular_items if self.v.get() == 'regular' else playoff_items
                    result_window = show_list_results(res, list(RP.keys()))
                    result_window.title('%s %s 查询结果' % (self.plyr_ent_value.get(), self.ROP_dict[self.v.get()]))
                    result_window.loop(' 共查询到%d条记录' % len(res))
                else:
                    messagebox.showinfo('提示', '未查询到符合条件的数据！')
        else:
            messagebox.showinfo('提示', '请选择比赛类型！')

    def loop(self):
        # 背景图片
        bg_img = Image.open('../images/wade&james.jpg')
        bg_img.putalpha(64)
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        # 控件设置
        plyr = Label(self.wd, text='球员:', font=('SimHei', self.fontsize),
                     width=self.col_w, height=1, anchor='e')
        plyr_ent = Entry(self.wd, width=15, textvariable=self.plyr_ent_value)
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=self.col_w*4, height=25, image=search_img,
                               compound='center', cursor='hand2',
                               command=self.search)
        r1 = Radiobutton(self.wd, text='常规赛', value='regular', command=self.selection,
                         variable=self.v, width=self.radiobutton_w, height=1)
        r2 = Radiobutton(self.wd, text='季后赛', value='playoff', command=self.selection,
                         variable=self.v, width=self.radiobutton_w, height=1)
        # 控件布局
        plyr.grid(padx=self.padding, pady=self.padding, row=1, column=0)
        plyr_ent.grid(padx=self.padding, pady=self.padding, row=1, column=1, columnspan=2)
        r1.grid(padx=self.padding, pady=self.padding, row=1, column=3)
        r2.grid(padx=self.padding, pady=self.padding, row=1, column=4)
        search_button.grid(padx=self.padding, pady=self.padding, row=1, column=5)
        # wd.attributes("-alpha", 0.8)
        self.wd.mainloop()


search_by_player_window = Search_by_plyr()
search_by_player_window.loop()
