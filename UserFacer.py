# coding=utf-8
import os
import sys
import tkinter as tk
import tkinter.messagebox as tkm
import tkinter.filedialog as tkf
import tkinter.ttk as ttk
import threading
import traceback
from Constant import *
from Merge import Merger

from typing import List, Union


class UserFacer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('MP4合并工具')
        self.root.geometry('530x350')
        self.root.update()
        self.error: List[Exception] = []
        self.processMessage: List[float] = []
        self.state: List[bool] = [AVAILABLE_FOR_MERGING]
        self.defaultOutFile = 'out.mp4'
        self.outFile = self.defaultOutFile
        self.files = []
        self.getTextHeight = lambda px: px // 20
        self.cross = False
        self.longFirst = False
        self.merger: Merger = None

        tk.Label(self.root, text='输出文件')
        self.outFileFrame = tk.Frame(self.root)
        self.outFileEntry = tk.Entry(self.outFileFrame)
        self.outFileEntry.insert(0, self.defaultOutFile)
        self.outFileLookThroughButton = tk.Button(self.outFileFrame, command=self.changeOut, text='浏览')
        tk.Label(self.root, text='被合并文件，多个文件用“;”分割')
        self.selectFrame = tk.Frame(self.root)
        self.selectFilesViewText = tk.Text(self.selectFrame)
        self.selectFilesButtonsFrame = tk.Frame(self.selectFrame)
        self.selectFilesButton = tk.Button(self.selectFilesButtonsFrame, command=self.selectFiles, text='选择文件')
        self.clearSelectButton = tk.Button(self.selectFilesButtonsFrame, command=self.clearSelect, text='清空选择')
        self.processBar = ttk.Progressbar(self.root, maximum=100)
        self.progressAnimate()
        self.startButton = tk.Button(self.root, command=self._thread_merge, text='开始合并')
        self.menu = tk.Menu(self.root)

        self.menu.add_command(label='help', command=self.help)
        self.menu.add_command(label='Crossly', command=self.toggleCross)
        self.menu.add_command(label='LongFirst', command=self.toggleLongFirst)
        self._childrenPack(self.outFileFrame, side=tk.LEFT)
        self._childrenPack(self.selectFrame)
        self._childrenPack(self.selectFilesButtonsFrame, side=tk.LEFT)
        self._childrenPack(self.root, expand=True)
        self._childrenPack(self.menu)

        self.processBar.pack_configure(expand=True, fill=tk.X)
        self.selectFilesViewText.pack_configure(expand=True, fill=tk.BOTH)
        self.selectFrame.pack_configure(expand=True, fill=tk.BOTH)
        # 绑定调整大小事件:ViewText缩放比例
        self.root.bind('<Configure>', lambda *a: self.selectFilesViewText.configure(
            height=self.getTextHeight(self.root.winfo_height() * 0.8)
        ))
        # 添加menu到root
        self.root.config(menu=self.menu)
        # 绑定点击事件：恢复进度条动画
        self.root.bind('<Button-1>', lambda *a: (self.progressAnimate() if self.state[0] == AVAILABLE_FOR_MERGING else None))

    def toggleCross(self):
        """调整是否交叉写帧"""
        self.cross = not self.cross
        tkm.showinfo(
            '状态切换',
            f'交叉写帧模式:{"开启" if self.cross else "关闭"}'
        )

    def toggleLongFirst(self):
        """调整是否严格模式"""
        self.longFirst = not self.longFirst
        tkm.showinfo(
            '状态切换',
            f'视频长度优先:{"最长" if self.longFirst else "最短"}'
        )

    @staticmethod
    def help():
        tkm.showinfo(
            '使用帮助',
            """
            使用方法：
                1、在输入栏输入或点击“浏览”按钮
                    填写输出文件的路径。
                2、在文本框内依次填写要被合并的mp4文件
                    或点击“选择文件”按钮。
                3、点击“开始合并”。
                4、等待进度条结束，弹出窗口，视频合成完毕。
            可用功能：
                1、帮助：
                    点击”help“即可获取本脚本的帮助信息。
                2、默认写帧模式：
                    按照选定文件顺序将文件完整合并，
                    点击”Crossly“切换默认写帧和交叉写帧模式。
                3、交叉写帧模式：
                    多个文件间轮流写帧，而不是整个文件合并，
                    此功能仅供娱乐。
                4、长度优先：
                    在交叉写帧模式下，长度优先为”最长“则输出视频长度
                    由被合并文件中的最长者决定，
                    反之亦然，点击”LongFirst“切换最长最短优先。
            注意事项：
                1、被合并文件不能是输出文件，否则输出视频可能乱码。
                2、暂不支持同一文件多次合并，
                    将会自动取消第二次同一文件的输入，
                    即同一文件只会被合并一次。
            创作者:azazo1
            """
        )

    @staticmethod
    def _childrenPack(wid: Union[tk.Widget, tk.Tk], **kwargs):
        for i in list(wid.children.values()):
            try:
                i.pack(**kwargs)
            except Exception as e:
                print(e, file=sys.stderr)

    def changeOut(self):
        t = tkf.asksaveasfilename()
        if t:
            self.outFile = t
            self.outFileEntry.delete(0, tk.END)
            self.outFileEntry.insert(0, self.outFile)

    def clearSelect(self):
        self.selectFilesViewText.delete(0.0, tk.END)
        self.analyzeText()
        print(f'Select Files changed to {self.files}')

    def selectFiles(self):
        fs = tkf.askopenfilenames()
        if not fs:
            return
        self.analyzeText()
        self.files.extend(fs)
        self.fillText()
        print(f'Selected Files changed to {self.files}')

    def analyzeText(self):
        """解析并保存ViewText中的文件"""
        s: str = self.selectFilesViewText.get(0.0, tk.END)
        if s:
            self.files = list(filter(lambda a: a, [i.strip() for i in s.split(';')]))

    def fillText(self):
        self.selectFilesViewText.delete(0.0, tk.END)
        self.selectFilesViewText.insert(0.0, (';\n'.join(self.files) + ';') if self.files else '')

    def checkState(self):
        if self.state[0] == MERGE_COMPLETED:
            t = tkm.askyesnocancel('合并完成',
                                   f'您的文件已保存到：{self.outFile}，是否打开文件？点击取消删除文件。')
            if t:
                os.system(self.outFile)
            elif t is None:
                os.remove(self.outFile)
            self.state[0] = AVAILABLE_FOR_MERGING
            self.startButton.config(command=self._thread_merge, text='开始合并')  # 改变开始按钮状态
        elif self.state[0] == START_MERGE:
            self.progressAnimate(False)
            self.startButton.config(command=lambda: self.shutdown(), text='中断合并')
            self.state[0] = MERGING

    def progressAnimate(self, start=True):
        if start:
            self.processBar.config(mode='indeterminate')
            self.processBar.start()
        else:
            self.processBar.config(mode='determinate')
            self.processBar.stop()

    def shutdown(self):
        """终端合并"""
        try:
            if tkm.askokcancel(
                    '确认？',
                    '是否要中断合并？操作无法撤销！'):
                self.merger.alive = False
                self.state[0] = AVAILABLE_FOR_MERGING
        except Exception:
            traceback.print_exc()

    def checkProcess(self, process: float = None):
        if process is not None and 0 <= process <= 1:  # 测试用
            self.processBar.stop()
            self.processBar.step(process * 100)
        elif self.processMessage:
            p = self.processMessage.pop(0) * 100
            self.processBar.stop()
            self.processBar.step(p)

    def _thread_merge(self):
        # 检查输出文件是否为空
        if not self.outFileEntry.get():
            tkm.showerror(
                '请输入文件名',
                '输出文件名不能为空！'
            )
            return
        # 通过ViewText获得选择文件
        self.analyzeText()
        print(f'Select Files changed to {self.files}')

        # 检查选择文件是否为空
        if not self.files:
            tkm.showerror(
                '请选择文件',
                '被合并的文件不能为空！'
            )
            return
        # 开始线程
        threading.Thread(target=self.merge).start()

    def merge(self):
        try:
            self.state[0] = START_MERGE
            self.merger = Merger(self.outFile, *self.files, cross=self.cross, longFirst=self.longFirst)
            self.merger.writeAllVideo(lambda n, t: self.processMessage.append(n / t))
            self.merger.close()
            self.state[0] = MERGE_COMPLETED
        except Exception as e:
            self.error.append(e)

    def checkError(self):
        if self.error:
            e = self.error.pop(0)
            tkm.showerror(f'{type(e)}', f'{e}')

    def go(self):
        try:
            self.help()
            while True:
                self.root.update()
                self.checkState()
                self.checkProcess()
                self.checkError()
        except tk.TclError as e:
            print(e, file=sys.stderr)
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    UserFacer().go()
