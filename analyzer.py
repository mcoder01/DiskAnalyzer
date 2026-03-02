import os
from concurrent.futures import ThreadPoolExecutor

class Analyzer(ThreadPoolExecutor):
    def scan(self, folder, parent, onupdate, onemptyfolder):
        def f():
            nonlocal folder, parent, onupdate, onemptyfolder
            try:
                with os.scandir(folder) as it:
                    empty = True
                    for entry in it:
                        size = entry.stat().st_size if entry.is_file() else None
                        onupdate.emit((parent, folder, entry.name, size))
                        empty = False

                    if empty:
                        onemptyfolder.emit(parent)
            except (NotADirectoryError, PermissionError):
                pass

        self.submit(f)