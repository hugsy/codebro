FROM django:python2-onbuild

RUN apt-get update && \
    apt-get install -y libclang1-3.4 python-clang-3.4 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app/codebro
ENV PYTHONPATH /usr/lib/python2.7/dist-packages/
RUN python manage.py syncdb
