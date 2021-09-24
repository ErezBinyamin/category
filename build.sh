#!/bin/bash
build() {
	local IMAGE_NAME=daniel3735928559/category
	docker build --no-cache -t ${IMAGE_NAME} .
	return $?
}

build $@
