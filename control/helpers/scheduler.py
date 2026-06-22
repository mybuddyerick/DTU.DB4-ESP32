import time
from config.timings import TIMINGS


class Task:
    def __init__(self, name, runnable, interval_ms, run_immediately=False, enabled=True):
        self.name = name
        self.runnable = runnable
        self.interval_ms = int(interval_ms)
        self.enabled = enabled

        now = time.ticks_ms()

        if run_immediately:
            self.last_run_ms = time.ticks_add(now, -self.interval_ms)
        else:
            self.last_run_ms = now

    def is_due(self, now_ms):
        if not self.enabled:
            return False

        next_run_ms = time.ticks_add(self.last_run_ms, self.interval_ms)
        return time.ticks_diff(now_ms, next_run_ms) >= 0

    def run(self):
        self.runnable()
        self.last_run_ms = time.ticks_add(self.last_run_ms, self.interval_ms)

    def set_interval(self, interval_ms, reset_timer=True):
        self.interval_ms = int(interval_ms)

        if reset_timer:
            self.last_run_ms = time.ticks_ms()

    def enable(self, reset_timer=True):
        self.enabled = True

        if reset_timer:
            self.last_run_ms = time.ticks_ms()

    def disable(self):
        self.enabled = False


class Scheduler:
    def __init__(self, step_interval_ms=TIMINGS["step"]):
        self.tasks = []
        self.step_interval_ms = int(step_interval_ms)

    def add(self, task):
        self.tasks.append(task)
        return task

    def every(self, name, interval_ms, runnable, run_immediately=False, enabled=True):
        task = Task(
            name=name,
            runnable=runnable,
            interval_ms=interval_ms,
            run_immediately=run_immediately,
            enabled=enabled
        )

        self.add(task)
        return task

    def step(self):
        now_ms = time.ticks_ms()

        for task in self.tasks:
            if task.is_due(now_ms):
                task.run()

    def wait(self):
        time.sleep_ms(self.step_interval_ms)

    def set_step_interval(self, step_interval_ms):
        self.step_interval_ms = int(step_interval_ms)

    def get(self, name):
        for task in self.tasks:
            if task.name == name:
                return task

        return None

    def set_task_interval(self, name, interval_ms, reset_timer=True):
        task = self.get(name)

        if task:
            task.set_interval(interval_ms, reset_timer)

        return task

    def enable_task(self, name, reset_timer=True):
        task = self.get(name)

        if task:
            task.enable(reset_timer)

        return task

    def disable_task(self, name):
        task = self.get(name)

        if task:
            task.disable()

        return task