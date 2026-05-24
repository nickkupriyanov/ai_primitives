# FastAPI FAQ Notes

## Q: What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It's built on Starlette and Pydantic, and it's one of the fastest Python frameworks available.

## Q: How do you define a route?

You use decorators like `@app.get("/path")` or `@app.post("/path")`. Each route takes a function that returns a response.

## Q: How does validation work?

FastAPI uses Pydantic models. When you declare a parameter with a Pydantic type, FastAPI automatically validates the request body against that model and returns detailed errors if validation fails.

## Q: How do you handle async?

FastAPI supports `async def` natively. Async endpoints run in an event loop, letting you use `await` for database queries, HTTP calls, and other I/O operations.

## Q: What is dependency injection in FastAPI?

FastAPI's `Depends()` function lets you declare dependencies that FastAPI resolves automatically. Dependencies can be functions, classes, or async callables. This is used for auth, database sessions, and configuration.
