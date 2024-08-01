# Installation

The first step is to install `HRL` in your machine.
 
It is recommended that you install HRL in a *python environment*. 
Using your favorite environment manager (*venv*, *pyenv*, *conda*, etc), 
run the following commands when *inside* the environment.
Make sure your enviroment runs **python 3**


## HRL for end-users

The easiest way to install HRL is using pip.

```bash
pip install https://github.com/computational-psychology/hrl/archive/master.zip
```

This will also install the required dependencies:
- [PyOpenGL](https://pyopengl.sourceforge.net/) (`pyopengl`)
- [PyGame](https://www.pygame.org/) (`pygame`)
- [NumPy](https://numpy.org/) (`numpy`)


## HRL for developers

First clone the repository 

```
git clone https://github.com/computational-psychology/hrl
```

Then go to the root of the repository and run

```
pip install -e .
```

This will make an editable installation, which reflects immediately your
changes in the source code and thus avoiding that you have to re-install the library
after every change you make.


## In the Lab

In addition to `HRL`, you need to install additional packages in the 
machine where you run your experiments in the lab.

### `pypixxlib` 

This propetary library is provided by Vpixx and it makes possible
to communicate with all Vpixx devices (Datapixx, ViewPixx, etc)


- Download the library from [Vpixx website](https://docs.vpixx.com/python/introduction-to-vpixx-python-documentation). 

- Install with

```
pip install PATH_TO_FILE/pypixxlib.tar.gz
```



### `pyserial`

Needed when using the [Minolta LS-100 photometer](https://www.konicaminolta.com/instruments/download/instruction_manual/light/pdf/ls-100-110_instruction_eng.pdf) for calibration. 
Install with

```
pip install pyserial
```
