#!/bin/bash

USAGE="""
Usage: ./build_coog_customers.sh VERSION CLIENT
	VERSION: the version you want to build
	You must precise only one version to build

	CLIENT: "--all" if you want to build image for each client in the customers file
			you can build only one client image by replacing --all by the client name

	ex: ./build_coog_customers.sh 2.0.30 --all
  """

#if there is no input
[ $# -ne 2 ] && echo "$USAGE" && exit 1

#if one of the variable is empty
[ -z "$1" ] && echo "Missing version number. $USAGE" && exit 1
[ -z "$2" ] && echo "Missing customers name. $USAGE" && exit 1

export DOCKER_BUILDKIT=1

major_version="$(cut -d'.' -f1 <<<"$1")"
minor_version="$(cut -d'.' -f2 <<<"$1")"
version="$major_version.$minor_version"

tag_version=$1

docker_import="coopengo/coog:$tag_version"

echo "$2"

#if we want to build image for every client
if [ $2 = "--all" ]
then
	file="customers"
	while IFS= read -r line
	do
		NAME=${line%:*}
		docker build --tag="coopengo/coog-$NAME:$tag_version" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$tag_version" --build-arg IMPORT="$docker_import" --build-arg VERSION="$version" --ssh default .
	done < "$file"

#if we want to build the image for one specific client
else 
	NAME="$2"
	docker build --tag="coopengo/coog-$NAME:$tag_version" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$tag_version" --build-arg IMPORT="$docker_import" --build-arg VERSION="$version" --ssh default .
fi