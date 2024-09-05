import multiprocessing
import threading


def run_on_thread(function):
    def wrap(*args, **kwargs):
        t = threading.Thread(target=function, args=args, kwargs=kwargs, daemon=True)
        t.start()

        return t
    return wrap


def run_on_process(function):
    def wrap(*args, **kwargs):
        process = multiprocessing.Process(target=function, args=args, kwargs=kwargs)
        process.start()
        return process 

    return wrap
