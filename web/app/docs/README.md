# Reach API Documentation

## How to contribute

### Requirements:
  - Python > 3.6
  - Virtualenv
  - Pip

### Install the documentation stack:

```
virtualenv env -p python3
source env/bin/activate
pip install -r requirements.txt
```

### Build the documentation

Sphinx accepts two types of files:
  - `.rst`: re:Structured files
  - `.md`: Markdown formatted files

While both are allowed, for consistency, writing .md files is recommended.
Once all files are written, add them by name to index.rst and run `make html`.
