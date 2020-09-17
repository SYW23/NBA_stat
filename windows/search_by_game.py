#!/usr/bin/python
# -*- coding:utf8 -*-

import sys

sys.path.append('../')
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from util import LoadPickle
from search_by_player import ShowSingleResults


class Search_by_game(object):
    def __init__(self):
        self.fontsize = 10
        self.font = ('SimHei', self.fontsize)
        self.col_w = 15
        self.radiobutton_w = 5
        self.paddingx = 10
        self.paddingy = 10
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
        self.season = StringVar()
        self.ROP = StringVar()
        self.ROP.set(None)
        self.qtr = StringVar()
        self.qtr.set('whole')
        self.sels = []
        self.wd = Frame(self.wd_)
        self.wd.grid()
        self.wd_.bind("<Return>", self.search_enter)
        self.radioframe = None

    def one_tick_sel(self, text, value, command, win):
        return Radiobutton(win, text=text, value=value, command=command,
                           variable=self.qtr, width=self.radiobutton_w, height=1)

    def season_cbox_sel(self, event):
        [i.grid_remove() for i in self.radioframe.grid_slaves()]
        if self.season.get()[:4] >= '1996':
            end = 8
        elif self.season.get()[:4] < '1983':
            end = 1
        else:
            end = 2
        for ix, i in enumerate(self.sels[:end]):
            i.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=ix)

    def search_enter(self, event):    # 绑定回车键触发搜索函数
        self.search()

    def search(self):
        print('功能尚未开放')

    def timespan(self):
        pass

    def ROPselection(self):
        pass

    def QTRselection(self):
        pass

    def loop(self):
        # 背景图片
        bg_img = Image.open('../images/james2.jpg')
        bg_img.putalpha(64)
        bg_img = ImageTk.PhotoImage(bg_img)
        Label(self.wd, image=bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        self.radioframe = Frame(self.wd)
        self.radioframe.grid(padx=self.paddingx, pady=self.paddingy, row=4, column=0, columnspan=5, sticky='ew')
        # 控件设置
        season_label = Label(self.wd, text='赛季:', font=self.font, width=self.col_w, height=1, anchor='e')
        season_sel = ttk.Combobox(self.wd, width=9, textvariable=self.season)
        season_sel['value'] = ['%d-%d' % (x, x + 1) for x in range(1949, 2020)]
        season_sel.current(len(season_sel['value']) - 1)
        timespan_frame = LabelFrame(self.wd, text='时间跨度', labelanchor="nw")
        sglssn_sel = self.one_tick_sel('单赛季', 'single_season', self.timespan, timespan_frame)
        tilnow_sel = self.one_tick_sel('至今', 'tillnow', self.timespan, timespan_frame)
        rf_frame = LabelFrame(self.wd, text='比赛类型', labelanchor="nw")
        rglr_sel = self.one_tick_sel('常规赛', 'regular', self.ROPselection, rf_frame)
        plyf_sel = self.one_tick_sel('季后赛', 'playoff', self.ROPselection, rf_frame)
        search_img = Image.open('../images/kobe_dunk.jpg')
        search_img = ImageTk.PhotoImage(search_img)
        search_button = Button(self.wd, text='查  询', width=65, height=30, image=search_img,
                               compound='center', cursor='hand2', command=self.search, font=('SimHei', 14))
        team_label = Label(self.wd, text='球队:', font=self.font, width=self.col_w, height=1, anchor='e')
        oppteam_label = Label(self.wd, text='对手球队:', font=self.font, width=self.col_w, height=1, anchor='e')
        team_ent = Entry(self.wd, width=10)
        oppteam_ent = Entry(self.wd, width=10)
        sel_texts = [['全场', 'whole'], ['进阶', 'advcd'], ['第一节', '1st'], ['第二节', '2nd'],
                     ['上半场', '1hf'], ['第三节', '3rd'], ['第四节', '4th'], ['下半场', '2hf']]
        for ts in sel_texts:
            self.sels.append(self.one_tick_sel(ts[0], ts[1], self.QTRselection, self.radioframe))

        # 控件布局
        season_label.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=0)
        season_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=1)
        season_sel.bind("<<ComboboxSelected>>", self.season_cbox_sel)
        timespan_frame.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=2)
        sglssn_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=0)
        tilnow_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=0)
        rf_frame.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=3)
        rglr_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=0)
        plyf_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=0)
        search_button.grid(padx=self.paddingx, pady=self.paddingy, row=1, rowspan=2, column=4, columnspan=2)
        team_label.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=0)
        oppteam_label.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=2)
        team_ent.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=1)
        oppteam_ent.grid(padx=self.paddingx, pady=self.paddingy, row=3, column=3)
        # whole_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=2, sticky='ew')
        # advcd_sel.grid(padx=self.paddingx, pady=self.paddingy, row=1, column=3, sticky='ew')
        # first_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=0, sticky='ew')
        # secnd_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=1, sticky='ew')
        # fsthf_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=2, sticky='ew')
        # third_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=3, sticky='ew')
        # forth_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=4, sticky='ew')
        # sndhf_sel.grid(padx=self.paddingx, pady=self.paddingy, row=2, column=5, sticky='ew')
        self.wd.mainloop()


search_by_game_window = Search_by_game()
search_by_game_window.loop()
