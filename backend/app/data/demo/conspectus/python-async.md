# Python Async Programming

## async/await

Python's `asyncio` library provides infrastructure for writing concurrent code using the `async`/`await` syntax.

```python
import asyncio

async def fetch_data(url):
    await asyncio.sleep(1)
    return f"Data from {url}"
```

## Event Loop

The event loop is the core of asyncio. It runs async tasks, handles I/O events, and schedules callbacks. Use `asyncio.run()` to start the event loop.

## GIL and Async

The GIL doesn't prevent asyncio from being useful for I/O-bound tasks. Async code yields control at `await` points, allowing other coroutines to run. For CPU-bound work, use `run_in_executor` or multiprocessing instead.

## Coroutines vs Threads

Coroutines are lighter than threads. Thousands of coroutines can run concurrently in a single thread. Threads are better for CPU-bound work (if GIL allows) or when calling blocking C extensions.
