@echo off
setlocal

REM Replace these values with the same values used in the lab.
set PROJECT_ID=YOUR_PROJECT_ID
set REGION=asia-south1
set SERVICE_ACCOUNT_NAME=dataproc-data-sa
set SERVICE_ACCOUNT_EMAIL=%SERVICE_ACCOUNT_NAME%@%PROJECT_ID%.iam.gserviceaccount.com
set BUCKET_NAME=YOUR_EXACT_BUCKET_NAME
set CLUSTER_NAME=dataproc-beginner-cluster
set VPC_NAME=dataproc-vpc
set SUBNET_NAME=dataproc-subnet
set FIREWALL_RULE=dataproc-allow-internal

echo Deleting Dataproc cluster...
gcloud dataproc clusters delete %CLUSTER_NAME% --region=%REGION% --project=%PROJECT_ID% --quiet

echo Deleting Cloud Storage bucket and all contents...
gcloud storage rm --recursive gs://%BUCKET_NAME%/

echo Deleting firewall rule...
gcloud compute firewall-rules delete %FIREWALL_RULE% --project=%PROJECT_ID% --quiet

echo Deleting subnet...
gcloud compute networks subnets delete %SUBNET_NAME% --region=%REGION% --project=%PROJECT_ID% --quiet

echo Deleting VPC...
gcloud compute networks delete %VPC_NAME% --project=%PROJECT_ID% --quiet

echo Deleting custom service account...
gcloud iam service-accounts delete %SERVICE_ACCOUNT_EMAIL% --project=%PROJECT_ID% --quiet

echo Cleanup commands completed. Review any "not found" message and verify in Google Cloud Console.
endlocal
