FROM django:python2-onbuild

RUN pip uninstall -y pydot

RUN apt-get update && \
    apt-get install -y libclang1-3.4 python-clang-3.4 python-pydot --no-install-recommends && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app/codebro
ENV PYTHONPATH /usr/lib/python2.7/dist-packages/

RUN python manage.py syncdb
