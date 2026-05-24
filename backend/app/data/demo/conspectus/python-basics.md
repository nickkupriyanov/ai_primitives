# Python Basics

## Variables and Types

Python is dynamically typed. You don't need to declare types. Variables are created when you assign a value to them.

```python
name = "Alice"
age = 30
height = 5.8
is_student = False
```

Python supports int, float, str, bool, list, tuple, dict, set types.

## Control Flow

Python uses indentation for code blocks. If statements, for loops, while loops — all use colons and indentation.

```python
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teenager")
else:
    print("Child")
```

## Functions

Functions are defined with `def`. They can have default arguments, keyword arguments, and variable-length arguments.

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"
```

## The GIL

The Global Interpreter Lock (GIL) is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecode at once. This means CPU-bound Python programs won't benefit from multi-threading.
