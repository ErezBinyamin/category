IMAGE=daniel3735928559/category

.PHONY:all
all: .img_build

.img_build: Dockerfile app/* 
	touch $@
	docker build -t $(IMAGE) .

run: .img_build
	docker run --volume $(pwd)/example/:/usr/src/app/example -it $(IMAGE) bash
