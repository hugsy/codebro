CodeBro!
========

What is it ?
------------

Web based code browser, using clang AST parser to create cross-reference between
function calls. For those interested, all this idea came from [Eli Bendersky's
website](http://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang/). 
Parsing AST makes it easy to spot trivial bugs, and using callgraph
makes it easier to focus on potential exploitability on this bug.

It is *NOT* built in any way for production use and do not make it reachable
from public Internet or "You're gonna have a bad time" ! 


Disclaimer
----------
* Code is dirty;
* Code is in release before-alpha, still under heavy development;
* If something's not working properly, try to hack it yourself and only when
you're sure it's bug, file it;
* X-refing and parsing are slow but won't over-charge your CPU;
* I don't advise to parse and x-ref *huge* source code trees, a better approach
would be to split it into sub-projects;

That being said, if you still wanna go further, read below. 


Requires
--------
* python 2.7+
* django 1.5
* pydot
* pygments
* llvm + clang (with python bindings)
* dajax & dajaxice

` $ pip2 install python-dajax && pip2 install python-dajaxice ` should do it in
most cases 

* a database to store data (sqlite, mysql, pgsql, etc.)


Install
-------
* Get and install clang-llvm, make sure Python bindings are compiled as well
(http://clang.llvm.org/get_started.html)

* Create a Python VirtualEnv and move to it
```
$ mkvirtualenv codebro
[...]
$ workon codebro
```

* Clone CodeBro and install pre-requisites
```
$ git clone https://github.com/hugsy/codebro.git && pip install -r codebro/requirements.txt
```

* Make sure it works :
```
$ python -c 'import django; import clang;' && echo 'Party can start now!'
```

* Create database structure, and fill with initial initial data :
```
$ ./manage.py syncdb
```

* Launch the server
```
$ ./manage.py runserver
```
* You can now add, browse and parse applications.

## License & Author
Written by @_hugsy_ and released under GPL v.2

