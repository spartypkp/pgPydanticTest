import time
import threading
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import json

class PyFileEventHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # If the file modified is "apply_codemod.py", don't do anything
            if event.src_path.endswith('apply_codemod.py'):
                return
            self.queue.put(event)

def worker(queue):
    while True:
        event = queue.get()
        if event is None:  # None is sent as a signal to stop the worker
            break
        # Your callback function goes here
        print(f"Detected change in: {event.src_path}")

        # Call apply_codemod.py with the detected filename
        subprocess.run(["python", "apply_codemod.py", event.src_path], check=True)
        
        queue.task_done()

def start_watching(path):
    queue = Queue()
    event_handler = PyFileEventHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    worker_thread = threading.Thread(target=worker, args=(queue,))
    worker_thread.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # Stop the worker thread
    queue.put(None)
    worker_thread.join()

with open('config.json') as f:
    config = json.load(f)
f.close()
srcDir = config['srcDir']
# Replace '/path/to/watch' with the path of the directory you want to watch
start_watching(srcDir)