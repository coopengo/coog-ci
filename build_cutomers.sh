#!/bin/bash

USAGE="""
Usage: ./report VERSION
	VERSION: the version you want to build for every client
	You must precise only one version to test
	ex : 2.0.30
  """
echo "$USAGE"

#if there is no input or too many inputs
[ $# -ne 1 ] && echo "$Usage" && exit 1

#if variable is empty
[ -z "$1" ] && echo "Missing version number. $USAGE" && exit 1

major_version="$(cut -d'.' -f1 <<<"$1")"
minor_version="$(cut -d'.' -f2 <<<"$1")" 
version="$major_version.$minor_version"

docker_import="coopengo/coog:coog-$version"

tag_version=$1

file="customers"

while IFS= read -r line
do
    NAME=${line%:*}
	docker build --tag="coopengo/coog-$NAME:$tag_version" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$tag_version" --build-arg IMPORT="$docker_import" --build-arg VERSION="$version" --ssh default .

done < "$file"
