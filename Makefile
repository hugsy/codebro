NAME = codebro
IMGNAME = $(NAME)
ACTIONS = help clean mrproper build run shell

help:
	echo "Usage: make $(ACTIONS)"

clean:
	docker ps -q -a -f name=$(NAME) | xargs docker rm -f

mrproper:
	docker images -q -a $(IMGNAME) | xargs docker rmi -f

build:
	docker build -t $(IMGNAME) .

run:
	docker run -d --name=$(NAME) -p 127.0.0.1:8000:8000 $(IMGNAME)

shell:
	docker exec -i -t $(NAME) /bin/bash

.PHONY: $(ACTIONS)
.SILENT: help
