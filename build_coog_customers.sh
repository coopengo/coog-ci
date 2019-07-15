#!/bin/bash

USAGE="""
Usage: ./build_coog_customers.sh -v TAG_VERSION -c CUSTOMER

	-v TAG_VERSION: The tag version you release.

	-c CUSTOMER: the customer you release version for.
	             use "--all" if you want to build image for every customers in "customers" file
  """

_get_version_from_tag(){
	major_version="$(cut -d'.' -f1 <<<"$1")"
	minor_version="$(cut -d'.' -f2 <<<"$1")"
	version="$major_version.$minor_version"
}

_get_docker_import(){
	DOCKER_IMPORT="coopengo/coog:$1"
}

_get_custom_repos(){
	read -r GIT_REPOS < "../coog-admin/images/coog/repos.custom"
	GIT_REPOS=${GIT_REPOS##*;}.git
	echo "$GIT_REPOS"
}

_build_image_customer(){
	if [ $1 = "--all" ]
	then
		file="customers"
	    while IFS= read -r line
	    do
	    	NAME=${line%:*}
	    	docker build --tag="coopengo/coog-$NAME:$2" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$2" --build-arg IMPORT="$DOCKER_IMPORT" --build-arg VERSION="$version" --build-arg CUSTOM_REPOS="$GIT_REPOS" --ssh default .
	    done < "$file"
	else
		echo "$1"
		NAME="$1"
		docker build --tag="coopengo/coog-$NAME:$2" --build-arg CUSTOMER="$NAME" --build-arg VERSION_TAG="$2" --build-arg IMPORT="$DOCKER_IMPORT" --build-arg VERSION="$version" --build-arg CUSTOM_REPOS="$GIT_REPOS" --ssh default .
	fi
}

main() {
	_get_version_from_tag $TAG_VERSION
	_get_docker_import $TAG_VERSION
	_get_custom_repos
	_build_image_customer $CUSTOMER $TAG_VERSION
}



#Script starts here
[ $# -lt 4 ] && echo "$USAGE" && exit 1

while [[ $# -gt 1 ]]; do

	arg="$1"
	value="$2"
	case $arg in
		-c|--customer)
            CUSTOMER="$value"
            shift
            ;;
        -v|--version)
            TAG_VERSION="$value"
            shift
            ;;
        *)
            echo "Invalid argument $arg."
            return 1
            ;;
    esac
    shift
done

#if one of the variable is empty
[ -z "$TAG_VERSION" ] && echo "Missing version number. $USAGE" && exit 1
[ -z "$CUSTOMER" ] && echo "Missing customers name. $USAGE" && exit 1

export DOCKER_BUILDKIT=1

main "$@"



