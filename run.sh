#!/bin/bash
run() {
	local IMAGE_NAME=daniel3735928559/category
	docker run --volume $(pwd)/example/:/usr/src/app/example -it ${IMAGE_NAME} bash
	return $?
}

run $@
