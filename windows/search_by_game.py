#!/usr/bin/python
# -*- coding:utf8 -*-

import sys

sys.path.append('../')
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from util import LoadPickle
from search_by_player import Show_list_results


class Search_by_game(object):
    def __init__(self):
        self.fontsize = 10
        self.col_w = 15
        self.radiobutton_w = 5
        self.padding = 10
        self.pm2pn = LoadPickle('../data/playermark2playername.pickle')
        self.pn2pm = dict(zip(self.pm2pn.values(), self.pm2pn.keys()))
        self.ROP_dict = {'regular': '常规赛', 'playoff': '季后赛'}
        self.wd_ = Tk()
        self.wd_.title('比赛数据查询器')
        self.wd_.iconbitmap('../images/nbahalfcourt.ico')
        # wd.resizable(width=True, height=True)
        self.wd_.geometry('+500+20')
        self.comboboxs = []
        self.stats = []
        # self.plyr_ent_value = StringVar()
        # self.plyr_ent_value.set('LeBron James')
        self.v = StringVar()
        self.v.set(None)
        self.wd = Frame(self.wd_)
        self.wd.grid()
        self.wd_.bind("<Return>", self.search_enter)

    def search_enter(self, event):    # 绑定回车键触发搜索函数
        self.search()

    def search(self):
        pass

    def loop(self):
        # 背景图片
        bg_img = Image.open('../images/james2.jpg')
        bg_img.putalpha(64)
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        # 控件设置
        season_label = Label(self.wd, text='赛季:', font=('SimHei', self.fontsize),
                             width=self.col_w, height=1, anchor='e')
        season = StringVar()
        season_sel = ttk.Combobox(self.wd, width=10, textvariable=season)
        season_sel['value'] = ['%d-%d' % (x, x + 1) for x in range(1996, 2020)]
        season_sel.current(len(season_sel['value']) - 1)
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=65, height=30, image=search_img,
                               compound='center', cursor='hand2', command=self.search, font=('SimHei', 14))

        # 控件布局
        season_label.grid(padx=self.padding, pady=self.padding, row=1, column=0)
        season_sel.grid(padx=self.padding, pady=self.padding, row=1, column=1, columnspan=2)
        search_button.grid(padx=self.padding, pady=self.padding, row=1, column=5)
        self.wd.mainloop()


search_by_game_window = Search_by_game()
search_by_game_window.loop()
