# Installation

## Users

The easiest way to install HRL is using pip.
It is not (yet) on PyPI, so first clone the repository via

```
git clone https://github.com/computational-psychology/hrl
```

Then go to the root of the repository and run

```
pip install .
```

```{note}
It is recommended that you install HRL in a *python environment*. 
Using your favorite env manager (venv, pyenv, conda, etc), run the `pip` command 
when *inside* the environment.
```



## Developers

If you want edit the source code and try changes, it is better that you do an 
editable installation. This will avoid that you have to re-install the library
after every change you do in the source code.

For this, append a `-e` to the pip command, in this way:

```
pip install -e .
```


