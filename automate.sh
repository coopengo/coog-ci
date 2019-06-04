#!/bin/bash

tag_version='2.0.30'
#tag_version=$1

file="image_name.txt"

for i in $(cat image_name.txt)

do docker build --tag="coopengo/coog-$i:$tag_version" --build-arg CUSTOMER="$i" --build-arg VERSION_TAG="$tag_version" --ssh default .

done

