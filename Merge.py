# coding=utf-8
import cv2
import os
import numpy as np


class Merger:
    def __init__(self, write_file: str, /, *files, cross=False, longFirst=False):
        """

        :param write_file:
        :param files:
        :param cross:  True：交叉写帧（帧画面交叉显现）；False：视频顺序写帧（视频完整）
        """
        self.alive = True
        self.cross = cross
        self.longFirst = longFirst
        self._files = list(files)
        self._videos = {}
        self.initFiles()
        self.width, self.height, self.fps, (self.totalFrames, self.countFrames) = self._getVideoInfo()
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
        if not self.cross or self.longFirst:
            total = self.totalFrames
        else:
            total = min(self.countFrames) * len(self.countFrames)

        for now, frame in enumerate(gen):
            self.writeFrame(frame)
            report(min(now, total - 1), total)
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
        countFrames = []
        for v in vs:
            t = v.get(cv2.CAP_PROP_FRAME_COUNT)
            totalFrames += t
            countFrames.append(t)
        return width, height, fps, (totalFrames, countFrames)

    def crosslyGenerateFrames(self):
        """It will pop videos out."""
        fail = set()
        try:
            while self.alive:
                for name, video in self._videos.items():
                    video: cv2.VideoCapture
                    success, frame = video.read()
                    if self.longFirst:
                        if len(fail) == len(self._videos):  # 长视频优先，视频长度由最长决定
                            return
                        elif not success:
                            print(f'Read {name} Over')
                            fail.add(video)
                        else:
                            yield frame
                    else:
                        if success:  # 短视频优先，视频长度由最短决定
                            yield frame
                        else:
                            return
            print('Reading Completed!')
        except Exception as e:
            raise e
        finally:
            self.close()

    def ordinarilyGenerateFrames(self):
        """It will pop videos out."""
        for name, video in self._videos.items():
            print(f'Reading:{name}...')
            success, frame = video.read()
            while self.alive and success:
                yield frame
                success, frame = video.read()
        print('Reading Completed!')
        self._videos.clear()

    def _openFile(self, f: str):
        if not os.path.exists(f):
            raise FileNotFoundError(f"Can't find '{f}'")
        self._videos.setdefault(f, cv2.VideoCapture(f))

    def close(self):
        self.alive = False
        try:
            self.writer.release()
        except AttributeError:
            pass
        for name, v in self._videos.items():
            v.release()
        self._videos.clear()

    def __del__(self):
        self.close()
