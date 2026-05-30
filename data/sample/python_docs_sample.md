# Virtual Environments and Packages

Python applications often use packages that are not part of the standard library. A
virtual environment keeps project dependencies isolated from the system Python
installation.

## Creating virtual environments

The `venv` module creates lightweight virtual environments. A common command is
`python -m venv .venv`. After creating the environment, activate it and install packages
with `python -m pip install`.

## Managing dependencies

Projects usually record their dependencies in a requirements file or project metadata so
the environment can be recreated later.
