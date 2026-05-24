# Python Language Overview B

Python is a multi-paradigm language that supports object-oriented, procedural, and functional programming styles.

## Type System

Python has an optional static type system through type hints. The `typing` module provides TypeVar, Generic, Protocol, and TypedDict that enable full static type checking with tools like mypy. Large codebases like Django and SQLAlchemy ship with type stubs. Python's type system continues to evolve with each release.

## Execution Model

Python compiles source code to bytecode before executing it on the Python Virtual Machine. The `.pyc` files you see in `__pycache__` directories are compiled bytecode. For performance, PyPy uses JIT compilation for frequently executed code paths, achieving near-C speeds for some workloads.
