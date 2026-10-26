import os
import time


def cleanup_old_files(directory: str, max_age_hours: float):
    if not os.path.isdir(directory):
        return
    cutoff = time.time() - max_age_hours * 3600
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass
