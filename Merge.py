# coding=utf-8
import cv2
import os
import numpy as np


class Merger:
    def __init__(self, write_file: str, /, *files, cross=False):
        """

        :param write_file:
        :param files:
        :param cross:  True：交叉写帧（帧画面交叉显现）；False：视频顺序写帧（视频完整）
        """
        self.cross = cross
        self._files = list(files)
        self._videos = {}
        self.initFiles()
        self.width, self.height, self.fps, self.totalFrames = self._getVideoInfo()
        self.writer = cv2.VideoWriter(write_file, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), self.fps,
                                      (self.width, self.height))

    def writeNextFrames(self, times: int):
        for t, frame in enumerate(self.ordinarilyGenerateFrames()):
            if t >= times:
                break
            self.writeFrame(frame)

    def writeFrame(self, frame: np.ndarray):
        w, h = frame.shape[1], frame.shape[0]
        if (w != self.width) or (h != self.height):
            raise ValueError(f'Wrong Size! invalid size:{(w, h)}, expected size:{(self.width, self.height)}!')
        self.writer.write(frame)

    def writeAllVideo(self, report=lambda now, total: None, end=lambda *a, **k: None):
        gen = self.ordinarilyGenerateFrames() if not self.cross else self.crosslyGenerateFrames()
        for t, frame in enumerate(gen):
            self.writeFrame(frame)
            report(t, self.totalFrames)
        end()

    def initFiles(self):
        for f in self._files:
            self._openFile(f)
        self._files.clear()

    def _getVideoInfo(self):
        vs = list(self._videos.values())
        v = vs[0]
        height = int(v.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(v.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(v.get(cv2.CAP_PROP_FPS))
        totalFrames = 0
        for v in vs:
            totalFrames += v.get(cv2.CAP_PROP_FRAME_COUNT)
        return width, height, fps, totalFrames

    def crosslyGenerateFrames(self):
        """It will pop videos out."""
        success = True
        while success:
            for name, video in self._videos.items():
                print(f'Reading:{name}...')
                video: cv2.VideoCapture
                success, frame = video.read()
                if success:
                    yield frame
                else:
                    break
        print('Reading Completed!')
        self._videos.clear()

    def ordinarilyGenerateFrames(self):
        """It will pop videos out."""
        for name, video in self._videos.items():
            print(f'Reading:{name}...')
            success, frame = video.read()
            while success:
                yield frame
                success, frame = video.read()
        print('Reading Completed!')
        self._videos.clear()

    def _openFile(self, f: str):
        if not os.path.exists(f):
            raise FileNotFoundError(f"Can't find '{f}'")
        self._videos.setdefault(f, cv2.VideoCapture(f))

    def close(self):
        try:
            self.writer.release()
        except AttributeError:
            pass
        for name, v in self._videos.items():
            v.release()
        self._videos.clear()

    def __del__(self):
        self.close()
