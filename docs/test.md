# How to run test
```sh
pytest
```

# How to enable print statement in pytest
```sh
pytest --capture=no
# Or pytest -s
```

# Pytest in verbose mode
```sh
pytest -v
```

# How to write tests
## unit test

### Step 1
Go to the unit folder under /tests

### Step 2
Create a test file that begin with "test" like
```
test_utils.py
```

### Step 3
Write test functions that begin with test like
```python
def test_rds():
    # test codes
```

## Integration/Acceptance Test
Acceptance test for flask is tricky. We use **unittest** class that can be integrated into pytest. I build a baseclass in tests/acceptance/test_bassclass.py
```python
"""
base class for pytest

alchemist

"""

import unittest
# import sh
from app import app


class TestBase(unittest.TestCase):
    def setUp(self):
        """
        start application test client, and login to linxiaow 
        This function runs once before each member function unit test.
        """
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
        somethin to restore
        like reset db if necessary
        """
        self.app_context.pop()

```
basically, setUp() will be called before each test, which is to set an app client. self.app will be all that you need.

## Step 1: create a file under acceptance folder begin with "test"
for example
```
test_login_logout.py
```

## Step 2: create a test class extending baseclass
for example:
```python
from .test_baseclass import TestBase

class TestRoot(TestBase):
```

with this, you can directly use the self.app to send requests then

## Step 3: creat functions that begin with "test"
for example:
```python
from .test_baseclass import TestBase


class TestRoot(TestBase):
    def test_root_directory(self):
        """
        GET /
        WHEN user go to / directory
        THEN welcome page should appear
        """
        response = self.app.get('/', content_type='html/text')
        
        self.assertEqual(
            response.status_code,
            200,
            "not able to get to root directory"
        )
```

when pytest is called in the command line, all functions begin with "test" will get called


# Difference between pytest and python -m pytest

```
Invoking pytest versus python -m pytest
Running pytest with pytest [...] instead of python -m pytest [...] yields nearly equivalent behaviour, except that the latter will add the current directory to sys.path, which is standard python behavior.

See also Calling pytest through python -m pytest.
```

https://docs.pytest.org/en/stable/pythonpath.html