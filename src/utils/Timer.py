import time

class Timer:

    def __init__(self):
        self._start_time = None
        self._end_time = None

    def start(self) -> None:
        self._start_time = time.time()
    
    def stop(self) -> None:
        self._end_time = time.time()
    
    def _elapsed(self) -> float:
        if self._start_time is None:
            raise ValueError("Timer has not been started.")
        if self._end_time is None:
            raise ValueError("Timer has not been stopped.")
        return self._end_time - self._start_time
    
    def cost(self) -> str:
        elapsed = self._elapsed()
        if elapsed < 60:
            return f"{elapsed:.2f}s"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            return f"{minutes}m{seconds:.2f}s"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = elapsed % 60
            return f"{hours}h{minutes}m{seconds:.2f}s"