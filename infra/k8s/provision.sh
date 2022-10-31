#!/usr/bin/env bash

~/populateSessionTokenProfile.sh badger default 107503

.SecurityGroups[].IpPermissions

aws ec2 describe-subnets --region eu-central-1
aws ec2 describe-instances --region eu-central-1
aws ec2 securoty-groups
aws ec2 --region eu-central-1 describe-security-groups --group-ids sg-00ea0d24bfcbe603e
aws ec2 --region eu-central-1 describe-security-groups --group-ids sg-08ee315b88a3ec35d
aws ec2 --region eu-central-1 describe-target-groups
aws elbv2 --region eu-central-1 describe-security-groups --group-ids sg-08ee315b88a3ec35d

aws elbv2 --region eu-central-1 describe-target-groups --names badgerdoc-tg
aws elbv2 --region eu-central-1 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-central-1:818863528939:targetgroup/badgerdoc-tg/4698ee0eb43f5b03

aws elbv2 --region eu-central-1 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:eu-central-1:818863528939:targetgroup/badgerdoc-tg/4698ee0eb43f5b03 --healthy-threshold-count 2

aws ec2 describe-instances --region eu-central-1
aws  --region eu-central-1 route53
aws  --region eu-central-1 route53 help

aws iam get-instance-profile --region eu-central-1 \
  --instance-profile-name orchestrator-default-ec2-profile
aws iam list-role-policies --region eu-central-1 \
  --role-name orchestrator-default-ec2-role
aws iam get-role-policy --region eu-central-1 --role-name orchestrator-default-ec2-role \
  --policy-name orchestrator-default-ec2-role

aws ecr --region eu-central-1 create-repository --repository-name badgerdoc/badgerdoc_ui \
  --tags 'Key=owner,Value=badgerdoc'

#https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policy-examples.html
aws ecr --region eu-central-1 set-repository-policy \
  --repository-name badgerdoc/badgerdoc_ui \
  --policy-text "$(cat registry_policy.json)"

aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS \
  --password-stdin 818863528939.dkr.ecr.eu-central-1.amazonaws.com

docker tag artifactory.epam.com:6144/badgerdoc/badgerdoc_ui_dev:0.1.0 \
  818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0

docker push 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0
docker pull 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0


kubectl create deployment badgerdoc-ui \
    --image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0
kubectl expose deployment badgerdoc-ui \
    --type=NodePort --port=5000

docker pull artifactory.epam.com:6144/badgerdoc/badgerdoc_ui_dev:0.1.0
docker tag artifactory.epam.com:6144/badgerdoc/badgerdoc_ui_dev:0.1.0 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0

aws ecr get-login-password --region eu-central-1 |   docker login --username AWS --password-stdin 818863528939.dkr.ecr.eu-central-1.amazonaws.com

docker push 818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/badgerdoc_ui:0.1.0


ssh to bastion



cat <<EOF | > .docker/config.json
'{
    "auths": {
        "872344130825.dkr.ecr.us-east-1.amazonaws.com": {
                "auth": "<awdawdawdawda>"
        }
    }
}'
EOF

sudo su -
under root
vi ~/.docker/config.json
