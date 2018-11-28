#!/usr/bin/env bash

#
# TEST, NOT USED, MAY NEED SOME REWRITING
#

# Configuration :
#
# pip install awscli
#
# La création des utilisateurs / accès se fait ici :
# https://console.aws.amazon.com/iam/home?#/users
#
# ===> aws configure
#
# ID : xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Clé : xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# region : eu-west-3
# format : text
#
#
# Création du groupe de sécurité (déjà créé, mais si nécessaire d'en faire un
# nouveau)
#
# ===> aws ec2 create-security-group --group-name devenv-sg \
#         --description "security group for development environment"
#
# <=== group_id
#
# Group ID : xxxxxxxxxxxxxxxxxxx
#
# Autorisations ssh :
#
# ===> aws ec2 authorize-security-group-ingress --group-name devenv-sg \
#         --protocol tcp --port 22 --cidr 0.0.0.0/0
#
# Création d'une paire de clés pour la connexion (la clé sera stockée dans
# "devenv-key.pem" :
#
# ===> aws ec2 create-key-pair --key-name devenv-key --query 'KeyMaterial' \
#         --output text > devenv-key.pem
# ===> chmod 400 devenv-key.pem


KEY_NAME="devenv-key"
GROUP_ID="xxxxxxxxxxxxxxxxx"
IMAGE_ID="xxxxxxxxxxxxxxxxx"
INSTANCE_TYPE="c5.2xlarge"

# Start instance
echo 'Starting instance'
INSTANCE_ID=$(aws ec2 run-instances --image-id "$IMAGE_ID" \
        --security-group-ids "$GROUP_ID" \
        --count 1 --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --query 'Instances[0].InstanceId')
echo "Instance Id: $INSTANCE_ID"

# Make sure we stop the instance in case of error, or when the script exits
function terminate {
    echo "Terminating instance $INSTANCE_ID"
    aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" \
        || >&2 echo "Error terminating $INSTANCE_ID, you may have to do it manually"
}
trap terminate EXIT

# Get instance ip
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress')
echo "Instance Ip: $INSTANCE_IP"

# Wait for startup
sleep 10

# Ssh connect
# This assumes the current directory has a "ssh" folder which contains a
# private / public key pair allowed to access the coog repositories
scp -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" -r ssh \
    ec2-user@"$INSTANCE_IP":~/ssh

echo "Starting up at $(date)"
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" ec2-user@"$INSTANCE_IP" \
    'bash -s' < run_tests_part1.sh

# Need to re-log in so that docker permissions are properly set
echo "Waiting for reboot, please wait"
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" ec2-user@"$INSTANCE_IP" \
    'sudo reboot -h now' || true

sleep 20

# Ip may have changed after reboot
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress')
echo "New instance Ip: $INSTANCE_IP"
ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" ec2-user@"$INSTANCE_IP" \
    'bash -s' < run_tests_part2.sh

echo "Terminating at $(date)"

ssh -o StrictHostKeyChecking=no -i "$KEY_NAME.pem" ec2-user@"$INSTANCE_IP"
