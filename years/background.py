import typing
import asyncio
import inspect


class BackgroundTask:
    def __init__(self, func: typing.Callable = None, *args, **kwargs):
        self.tasks = []
        if func is not None:
            self.tasks.append((func, args, kwargs))

    def add_task(self, func: typing.Callable, *args, **kwargs):
        self.tasks.append((func, args, kwargs))

    async def __call__(self):
        for task in self.tasks:
            func, args, kwargs = task
            if inspect.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                await asyncio.to_thread(func, *args, **kwargs)
