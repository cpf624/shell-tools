#!/usr/bin/env python
#encoding:utf-8
# Author:   jhat
# Date:     2014-01-12
# Email:    cpf624@126.com
# Home:     http://pfchen.org
# Vim:      tabstop=4 shiftwidth=4 softtabstop=4
# Describe: 目录实时同步

import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileSyncHandler(FileSystemEventHandler):

    """
    文件同步
    将指定目录的操作同步至另一个目录
    """

    def __init__(self, from_path, to_path):
        if not os.path.exists(from_path):
            raise OSError('not exists of from_path %s' % from_path)
        if not os.path.exists(to_path):
            # raise OSError('not exists of to_path %s' % to_path)
            os.mkdir(to_path)
        if not os.path.isdir(from_path):
            raise OSError('it\'s not a directory of from_path %s' % from_path)
        if not os.path.isdir(to_path):
            raise OSError('it\'s not a directory of to_path %s' % to_path)
        self._from_path = os.path.abspath(from_path)
        self._to_path = os.path.abspath(to_path)
        if self._to_path.startswith(self._from_path):
            raise OSError('to_path %s should not be under from_path %s' % (to_path, from_path))
        self._from_path_len = len(self._from_path) + 1
 
    def on_moved(self, event):
        """
        文件移动事件监听
        无法监听文件从监听目录移出的事件
        """

        if event.src_path is None:
            # 从监听目录之外移动文件至监听目录
            src = event.dest_path[self._from_path_len:]
            dest = os.path.join(self._to_path, src)
            if event.is_directory:
                os.makedirs(dest)
            elif os.path.exists(event.dest_path):
                self.copyfile(event.dest_path, dest)
            self.sync_stat(event.dest_path, dest)
        else:
            # 监听目录内移动文件
            src = event.src_path[self._from_path_len:]
            dest = event.dest_path[self._from_path_len:]
            src = os.path.join(self._to_path, src)
            dest = os.path.join(self._to_path, dest)
            # move 事件会递归产生，只需要响应最上层的move事件
            if os.path.exists(src) and not os.path.exists(dest):
                shutil.move(src, dest)

    def on_created(self, event):
        src = event.src_path[self._from_path_len:]
        dest = os.path.join(self._to_path, src)
        if event.is_directory:
            # 删除已存在的目标目录
            if os.path.exists(dest):
                os.rmdir(dest)
            os.makedirs(dest)
        elif os.path.exists(event.src_path):
            self.copyfile(event.src_path, dest)
        self.sync_stat(event.src_path, dest)

    def on_deleted(self, event):
        src = event.src_path[self._from_path_len:]
        dest = os.path.join(self._to_path, src)
        if os.path.exists(dest):
            if event.is_directory:
                os.rmdir(dest)
            else:
                os.remove(dest)

    def on_modified(self, event):
        src = event.src_path[self._from_path_len:]
        dest = os.path.join(self._to_path, src)
        if not event.is_directory and os.path.exists(event.src_path):
            self.copyfile(event.src_path, dest)
        self.sync_stat(event.src_path, dest)

    def copyfile(self, src_path, dest_path):
        """
        文件复制

        @param src_path 源文件
        @param dest_path 目标文件
        """

        if not os.path.exists(src_path):
            return
        p, f = os.path.split(dest_path)
        if not os.path.exists(p):
            os.makedirs(p)
        shutil.copyfile(src_path, dest_path)

    def sync_stat(self, src_path, dest_path):
        """
        文件属性同步

        @param src_path 源文件
        @param dest_path 目标文件
        """

        if os.path.exists(src_path) and os.path.exists(dest_path):
            stat = os.stat(src_path)
            os.chmod(dest_path, stat.st_mode)
            os.chown(dest_path, stat.st_uid, stat.st_gid)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print 'Usage: python filesync.py from_path to_path'
        sys.exit(0)
    from_path = sys.argv[1]
    to_path = sys.argv[2]
    event_handler = FileSyncHandler(from_path, to_path)

    # 检查是否已有同样的监听，如果没有则进行记录
    import tempfile, fcntl
    tmpdir = tempfile.gettempdir()
    record_file = os.path.join(tmpdir, 'filesync')
    record_sync = from_path + to_path + os.linesep
    record = None
    record_lock = open(os.path.join(tmpdir, 'filesync.lock'), 'w')
    fcntl.flock(record_lock, fcntl.LOCK_EX)
    if os.path.exists(record_file):
        record = open(record_file, 'rw+')
        for line in record.readlines():
            if line == record_sync:
                print 'already has sync from %s to %s' % (from_path, to_path)
                sys.exit(0)
    else:
        record = open(record_file, 'w')
    record.write(record_sync)
    record.close()
    fcntl.flock(record_lock, fcntl.LOCK_UN)

    observer = Observer()
    observer.schedule(event_handler, path = from_path, recursive = True)
    observer.start()

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # 退出运行后删除监听记录
    tmp = []
    fcntl.flock(record_lock, fcntl.LOCK_EX)
    record = open(record_file, 'r')
    for line in record.readlines():
        if line != record_sync:
            tmp.append(line)
    record.close()
    record = open(record_file, 'w')
    record.write(''.join(tmp))
    record.close()
    fcntl.flock(record_lock, fcntl.LOCK_UN)
