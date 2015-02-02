# CodeBro!


## What is it ?

Web based code browser, using clang AST parser to create cross-reference between
function calls. For those interested, all this idea came from [Eli Bendersky's
website](http://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang/). 
Parsing AST makes it easy to spot trivial bugs, and using callgraph
makes it easier to focus on potential exploitability on this bug.

It is *NOT* built in any way for production use and do not make it reachable
from public Internet or "You're gonna have a bad time" ! 


### Disclaimer

* Code is dirty;
* Code is in release before-alpha, still under heavy development;
* If something's not working properly, try to hack it yourself and only when
you're sure it's bug, file it;
* X-refing and parsing are slow but won't over-charge your CPU;
* I don't advise to parse and x-ref *huge* source code trees, a better approach
would be to split it into sub-projects;

That being said, if you still wanna go further, read below. 


## Requires
* LLVM + Clang (with Python bindings)
* Python 2.7+ (but not Python 3.x)
* Django 1.5
* PyDot + PyGraphViz (for graph generation)
* Pygments (for syntax colorization)
* dajax + dajaxice (for Ajax)
* any DBMS compatible with Django (for data storage)


## Install

### Using docker (recommended)
* Install docker
* Clone codebro repository
```
$ git clone https://github.com/hugsy/codebro.git && cd codebro
```
* Build the `codebro` image automagically (go grab a coffee though)
```
$ docker build -t codebro-docker-image .
```
* Run it in a detach instance, binding `codebro` listening
```
$ docker run --name codebro -p 8000:8000 -d codebro-docker-image
```

That's all folks !

### Manually 
* Get and install `llvm` engine and `clang` compiler. Make sure Python bindings are compiled as well
(http://clang.llvm.org/get_started.html)

* Add the path to the Python Clang bindings to `$PYTHONPATH`

* (optional but recommanded) Create a dedicated Python VirtualEnv and move in it
```
$ mkvirtualenv codebro
$ workon codebro
```

* Clone CodeBro and install pre-requisites
```
$ git clone https://github.com/hugsy/codebro.git && pip install -r codebro/requirements.txt
```

* Make sure it works 
```
$ python -c 'import django; import clang;' && echo 'Party can start now!'
```

* Move inside `codebro` directory, create database structure, and fill with initial initial data :
```
$ cd codebro
$ ./manage.py syncdb
```

* Launch the server
```
$ ./manage.py runserver
```
* You can now add, browse and parse applications.

## License & Author
Written by @_hugsy_ and released under GPL v2

