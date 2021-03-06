# coding=utf-8
import os
import sys

needs = ['opencv-python']

logName = 'Logs.txt'
print('Start')
state = 1
for p in sys.path:
    for module in needs:
        print(f'Installing:{module}')
        os.chdir(p)
        state = (os.system(f'python -m '
                           f'pip install {module} '
                           f'-i https://pypi.douban.com/simple '
                           f'>>{logName}')
                 and state)
    if state == 0:  # 成功安装
        break
print('Over')
os.system('pause')
