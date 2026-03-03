from queue import Queue
from threading import Thread

class ThreadPool:
    def __init__(self, size):
        self.tasks = Queue()
        for _ in range(size):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            func, args = self.tasks.get()
            try:
                func(*args)
            finally:
                self.tasks.task_done()

    def submit(self, func, *args):
        self.tasks.put((func, args))
