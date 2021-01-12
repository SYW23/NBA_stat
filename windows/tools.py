import sys
sys.path.append('../')
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import numpy as np
import math
from util import LoadPickle, gameMarkToDir, writeToPickle


class GameDetailEditor(object):
    def __init__(self, gm='201904050UTA', title='play-by-play修改器', st=''):
        self.title = title
        self.columns = ['时间', '客队记录', 'r', '比分', 'h', '主队记录']
        self.col_widths = [100, 400, 60, 100, 60, 400]
        self.wd_gd = Tk()
        self.wd_gd.geometry('1200x950+550+50')
        self.tree = None
        self.gm = StringVar()
        self.gm.set(gm)
        self.ori = StringVar()
        # self.ori.set('Violation by Team')
        self.tar = StringVar()
        if st:
            self.tar.set(st)
            self.ori.set('all')
        self.clock_o = StringVar()
        self.clock_o.set('')
        self.clock_n = StringVar()
        self.clock_n.set('')
        self.wd_gd.bind("<Return>", self.display_pbp_enter)
        self.wd_gd.bind("<Escape>", self.xquit)
        self.wd_gd.bind("<space>", self.xwrite2file)
        self.gameflow = None
        self.RoW_button = None
        self.RoW_int = 0    # 0阅读1编辑
        self.ori_qtr = 0
        self.qtr = StringVar()
        self.qtr.set(None)
        self.qtrs = 0
        self.qtr_fm = LabelFrame(self.wd_gd, text='节次', labelanchor='nw')
        self.qtr_btns = []
        self.qtr_text = ['1st', '2nd', '3rd', '4th', 'OT1', 'OT2', 'OT3', 'OT4']
        self.select_rows = [0, []]
        self.all_rows = 0
        self.file_name = None

    def xquit(self, event):
        self.wd_gd.destroy()

    def xwrite2file(self, event):
        self.write2file()

    def RoW(self):
        self.RoW_int = 0 if self.RoW_int else 1
        self.RoW_button['text'] = '编辑模式 点击切换' if self.RoW_int else '阅读模式 点击切换'
        print('开放编辑' if self.RoW_int else '不可编辑')

    def qtr_redsp(self):
        items = self.tree.get_children()
        [self.tree.delete(item) for item in items]
        self.insert_table(self.tree, self.gameflow[int(self.qtr.get())])
        self.all_rows += len(self.gameflow[int(self.qtr.get())])

    def reset_selection(self):
        self.select_rows[0] = 0
        self.select_rows[1] = []

    def qtr_dsp(self, ori=0):
        self.reset_selection()
        print('正在查看第%d节' % (int(self.qtr.get()) + 1))
        items = self.tree.get_children()
        [self.tree.delete(item) for item in items]
        self.insert_table(self.tree, self.gameflow[int(self.qtr.get())])
        # print(self.gameflow[int(self.qtr.get())])
        if not ori:
            self.all_rows += len(self.gameflow[self.ori_qtr])
        self.ori_qtr = int(self.qtr.get())

    def ofdefexc_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        ind = 1 if rec[1] else 5
        flag = 1
        if 'Offensive rebound' in rec[ind]:
            rec[ind] = rec[ind].replace('Offensive rebound', 'Defensive rebound')
            self.gameflow[int(self.qtr.get())][self.select_rows[1][0]] = rec
        elif 'Defensive rebound' in rec[ind]:
            rec[ind] = rec[ind].replace('Defensive rebound', 'Offensive rebound')
            self.gameflow[int(self.qtr.get())][self.select_rows[1][0]] = rec
        else:
            flag = 0
            print('无篮板纪录')
        if flag:
            self.qtr_redsp()
        self.reset_selection()

    def exc1with5_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        rec[1], rec[5] = rec[5], rec[1]
        self.gameflow[int(self.qtr.get())][self.select_rows[1][0]] = rec
        self.qtr_redsp()
        self.reset_selection()

    def top_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        # ind = 1 if rec[1] else 5
        self.gameflow[int(self.qtr.get())].pop(self.select_rows[1][0])
        self.gameflow[int(self.qtr.get())].insert(1, rec)
        self.qtr_redsp()
        self.reset_selection()

    def replace_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        ind = 1 if rec[1] else 5
        if self.ori.get() == 'all':
            if len(rec) == 2:
                assert ind == 1
                rec[ind] = rec[ind].replace(rec[ind], self.tar.get())
                rec.append('')
                rec.append(self.gameflow[int(self.qtr.get())][self.select_rows[1][0] - 1][3])
                rec.append('')
                rec.append('')
            else:
                rec[ind] = rec[ind].replace(rec[ind], self.tar.get())    # Violation by kaminfr01 (jump ball)
        elif self.ori.get() == 'p':
            player_rd = rec[ind].split(' ')[-1 if 'by' in rec[ind] else 0]
            if self.tar.get():
                rec[ind] = rec[ind].replace(player_rd, self.tar.get())
        else:
            rec[ind] = rec[ind].replace(self.ori.get(), self.tar.get())
        self.gameflow[int(self.qtr.get())][self.select_rows[1][0]] = rec
        self.qtr_redsp()
        self.reset_selection()

    def clock_alter_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        rec[0] = rec[0].replace(self.clock_o.get(), self.clock_n.get())
        self.gameflow[int(self.qtr.get())][self.select_rows[1][0]] = rec
        self.qtr_redsp()
        self.reset_selection()

    def insert_fc(self):
        assert self.select_rows[0] == 1
        rec = self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
        disc = self.tar.get()
        if 'Jump ball:' in disc:
            tmp = rec.copy()
            tmp[1] = disc
        else:
            ind = 1 if rec[1] else 5
            tmp = [x if x != rec[ind] else disc for x in rec]
            tmp[2], tmp[4], = '', ''
        if self.title != 'play-by-play修改器':
            tmp[0] = self.title.split(' ')[1][2:]
        self.gameflow[int(self.qtr.get())].insert(self.select_rows[1][0] + 1, tmp)
        self.qtr_redsp()
        self.reset_selection()
        self.all_rows -= 1

    def pop_fc(self):
        assert self.select_rows[0] == 1
        self.gameflow[int(self.qtr.get())].pop(self.select_rows[1][0])
        self.qtr_redsp()
        self.reset_selection()
        self.all_rows += 1

    def click(self, event):
        if self.RoW_int:
            print(self.all_rows)
            if self.select_rows[0] == 0:
                print('第%s节，第%d行' % (self.qtr.get(), int(self.tree.selection()[0][1:], 16) - 1 - self.all_rows))
                self.select_rows[0] += 1
                self.select_rows[1].append(int(self.tree.selection()[0][1:], 16) - 1 - self.all_rows)
            else:
                self.select_rows[0] += 1
                self.select_rows[1].append(int(self.tree.selection()[0][1:], 16) - 1 - self.all_rows)
                # 交换两行
                print('第%s节，第%d行' % (self.qtr.get(), int(self.tree.selection()[0][1:], 16) - 1 - self.all_rows))
                self.gameflow[int(self.qtr.get())][self.select_rows[1][0]], self.gameflow[int(self.qtr.get())][self.select_rows[1][1]] = \
                    self.gameflow[int(self.qtr.get())][self.select_rows[1][1]], self.gameflow[int(self.qtr.get())][self.select_rows[1][0]]
                self.qtr_redsp()
                self.reset_selection()

    def display_pbp_enter(self, event):
        self.display_pbp()

    def display_pbp(self):
        gm = self.gm.get()
        if gm:
            try:
                self.gameflow = LoadPickle(gameMarkToDir(gm, 'regular'))
                self.file_name = gameMarkToDir(gm, 'regular')
            except:
                self.gameflow = LoadPickle(gameMarkToDir(gm, 'playoff'))
                self.file_name = gameMarkToDir(gm, 'playoff')
            try:
                box = LoadPickle(gameMarkToDir(gm, 'regular', tp=2))
            except:
                box = LoadPickle(gameMarkToDir(gm, 'playoff', tp=2))
            # self.columns[1], self.columns[5] = ts[0], ts[1]
            print(box[0])
            self.qtrs = len(self.gameflow)
            self.qtr_btns = []
            for i in range(self.qtrs):
                self.qtr_btns.append(Radiobutton(self.qtr_fm, text=self.qtr_text[i], value=i, command=self.qtr_dsp,
                                                 variable=self.qtr, width=10, height=2))
                self.qtr_btns[i].grid(row=1, column=i)
            if self.title == 'play-by-play修改器':
                self.qtr.set('0')
            else:
                self.qtr.set(str(int(self.title[1]) - 1))
                self.RoW()
            self.qtr_dsp(ori=1)
        else:
            messagebox.showinfo('提示', '请输入game mark！')
        pass

    def write2file(self):
        if self.gameflow and self.file_name:
            writeToPickle(self.file_name, self.gameflow)
            print('写入文件%s成功' % self.file_name)
        else:
            messagebox.showinfo('提示', '没有内容！')

    def insert_table(self, tr, tb):
        for ix, i in enumerate(self.columns):  # 定义各列列宽及对齐方式
            tr.column(i, width=self.col_widths[ix], anchor='center')
            tr.heading(i, text=i)
        for i, r in enumerate(tb):    # 逐条插入数据
            tr.insert('', i, text=str(i), values=tuple(r))

    def tree_generate(self, tb):
        self.insert_table(self.tree, tb)    # 结果罗列表
        scrollbarx = Scrollbar(self.wd_gd, orient='horizontal', command=self.tree.xview)    # 滚动条
        self.tree.configure(xscrollcommand=scrollbarx.set)
        scrollbary = Scrollbar(self.wd_gd, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbary.set)
        # scrollbary.configure(command=self.tree.yview)
        # scrollbary.set(0.5, 0.5)
        # print(self.tree.yview())
        scrollbarx.place(relx=0.005, rely=0.97, relwidth=0.97, relheight=0.03)    # 布局
        scrollbary.place(relx=0.98, rely=0.25, relwidth=0.02, relheight=0.76)
        self.tree.place(relx=0.005, rely=0.25, relwidth=0.97, relheight=0.72)

    def clear_fc(self):
        self.gameflow = None
        self.tree = ttk.Treeview(self.wd_gd, columns=self.columns, show='headings')
        self.tree.bind('<ButtonRelease-1>', self.click)
        self.tree_generate([])
        self.qtr_btns = []
        self.select_rows = [0, []]
        self.all_rows = 0
        self.file_name = None
        # self.ori.set('Violation by Team')
        # self.tar.set('Turnover by ')
        self.clock_o.set('')
        self.clock_n.set('')
        if self.RoW_int:
            self.RoW()

    def loop(self):  # 参数：结果说明文字
        gm_label = Label(self.wd_gd, text='Game Mark', font=('SimHei', 13), width=15, height=1, anchor='e')
        gm_ent = Entry(self.wd_gd, width=20, textvariable=self.gm, font=('SimHei', 13))
        display_button = Button(self.wd_gd, text='读取', width=40, height=20,
                                compound='center', cursor='hand2', command=self.display_pbp, font=('SimHei', 14))
        write_to_button = Button(self.wd_gd, text='写入', width=40, height=20,
                                 compound='center', cursor='hand2', command=self.write2file, font=('SimHei', 14))
        self.RoW_button = Button(self.wd_gd, text='阅读模式 点击切换', width=100, height=20,
                                 compound='center', cursor='hand2', command=self.RoW, font=('SimHei', 13))
        clear_button = Button(self.wd_gd, text='清除', width=100, height=20,
                             compound='center', cursor='hand2', command=self.clear_fc, font=('SimHei', 13))
        ofdefexc_button = Button(self.wd_gd, text='攻防板', width=100, height=20,
                                compound='center', cursor='hand2', command=self.ofdefexc_fc, font=('SimHei', 13))
        exc1with5_button = Button(self.wd_gd, text='交换', width=100, height=20,
                                compound='center', cursor='hand2', command=self.exc1with5_fc, font=('SimHei', 13))
        top_button = Button(self.wd_gd, text='top', width=100, height=20,
                                  compound='center', cursor='hand2', command=self.top_fc, font=('SimHei', 13))
        replace_button = Button(self.wd_gd, text='replace', width=100, height=20,
                                  compound='center', cursor='hand2', command=self.replace_fc, font=('SimHei', 13))
        insert_button = Button(self.wd_gd, text='insert', width=100, height=20,
                               compound='center', cursor='hand2', command=self.insert_fc, font=('SimHei', 13))
        pop_button = Button(self.wd_gd, text='delete', width=100, height=20,
                            compound='center', cursor='hand2', command=self.pop_fc, font=('SimHei', 13))
        clock_button = Button(self.wd_gd, text='clock', width=100, height=20,
                                compound='center', cursor='hand2', command=self.clock_alter_fc, font=('SimHei', 13))

        tar_ent = Entry(self.wd_gd, width=20, textvariable=self.tar, font=('SimHei', 13))
        ori_ent = Entry(self.wd_gd, width=20, textvariable=self.ori, font=('SimHei', 13))
        clock_o_ent = Entry(self.wd_gd, width=20, textvariable=self.clock_o, font=('SimHei', 13))
        clock_n_ent = Entry(self.wd_gd, width=20, textvariable=self.clock_n, font=('SimHei', 13))

        gm_label.place(relx=0.02, rely=0.04, relwidth=0.1, relheight=0.04)
        gm_ent.place(relx=0.15, rely=0.04, relwidth=0.2, relheight=0.04)
        display_button.place(relx=0.38, rely=0.04, relwidth=0.08, relheight=0.04)
        write_to_button.place(relx=0.49, rely=0.04, relwidth=0.08, relheight=0.04)
        self.RoW_button.place(relx=0.81, rely=0.04, relwidth=0.18, relheight=0.04)
        clear_button.place(relx=0.6, rely=0.04, relwidth=0.08, relheight=0.04)
        ofdefexc_button.place(relx=0.71, rely=0.04, relwidth=0.08, relheight=0.04)
        exc1with5_button.place(relx=0.71, rely=0.09, relwidth=0.08, relheight=0.04)
        top_button.place(relx=0.81, rely=0.09, relwidth=0.08, relheight=0.04)
        replace_button.place(relx=0.91, rely=0.09, relwidth=0.08, relheight=0.04)
        insert_button.place(relx=0.71, rely=0.14, relwidth=0.08, relheight=0.04)
        pop_button.place(relx=0.81, rely=0.14, relwidth=0.08, relheight=0.04)
        ori_ent.place(relx=0.3, rely=0.19, relwidth=0.2, relheight=0.04)
        tar_ent.place(relx=0.52, rely=0.19, relwidth=0.47, relheight=0.04)
        clock_button.place(relx=0.91, rely=0.14, relwidth=0.08, relheight=0.04)
        clock_o_ent.place(relx=0.02, rely=0.19, relwidth=0.08, relheight=0.04)
        clock_n_ent.place(relx=0.12, rely=0.19, relwidth=0.08, relheight=0.04)

        self.wd_gd.title(self.title)
        self.qtr_fm.place(relx=0.01, rely=0.09, relwidth=0.65, relheight=0.08)
        self.tree = ttk.Treeview(self.wd_gd, columns=self.columns, show='headings')
        self.tree.bind('<ButtonRelease-1>', self.click)
        self.tree_generate([])
        self.display_pbp()
        self.wd_gd.mainloop()


if __name__ == '__main__':
    playbyplay_editor_window = GameDetailEditor()
    playbyplay_editor_window.loop()
