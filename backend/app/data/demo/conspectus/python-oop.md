# Python OOP

## Classes

Python classes are defined with `class` keyword. The `__init__` method is the constructor.

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
```

## Inheritance

Python supports single and multiple inheritance. Use `super()` to call parent methods.

```python
class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id
```

## Dunder Methods

Special methods with double underscores: `__str__`, `__repr__`, `__eq__`, `__lt__`, `__len__`, `__getitem__`. These enable operator overloading and integration with Python built-ins.

## Type Hints and Static Typing

Python 3.5+ supports optional type hints. While Python remains dynamically typed at runtime, type checkers like mypy and pyright can catch type errors before execution. Python also supports TypeVar for generics, Protocol for structural subtyping, and TypedDict for typed dictionaries.
