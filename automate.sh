#!/bin/bash

tag_version='2.0.30'
#tag_version=$1

file="customers"

while IFS= read -r line
do
       	NAME=${line%:*}
	docker build --tag="coopengo/coog-$NAME:$tag_version" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$tag_version" --ssh default .

done < "$file"

