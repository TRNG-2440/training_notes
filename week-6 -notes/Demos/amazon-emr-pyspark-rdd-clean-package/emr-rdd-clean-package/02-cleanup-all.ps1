#requires -Version 5.1
<#
02-cleanup-all.ps1

Deletes the resources created by 01-create-run-emr.ps1.
By default it reads the latest state file recorded in latest-state.txt.

Optional:
.\02-cleanup-all.ps1 -StateFile ".\emr-resource-state-YYYYMMDDHHMMSS.json"
#>

param(
    [string]$StateFile = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([Parameter(Mandatory=$true)][string]$Message)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Invoke-Aws {
    param(
        [Parameter(Mandatory=$true)][string[]]$AwsArgs,
        [Parameter(Mandatory=$true)][string]$Operation,
        [switch]$AllowFailure,
        [switch]$ShowOutput
    )

    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $ResultLines = & aws @AwsArgs 2>&1
        $ExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousPreference
    }

    $ResultText = ($ResultLines | ForEach-Object { "$_" }) -join [Environment]::NewLine

    if ($ShowOutput -and -not [string]::IsNullOrWhiteSpace($ResultText)) {
        Write-Host $ResultText
    }

    if ($ExitCode -ne 0 -and -not $AllowFailure) {
        if (-not [string]::IsNullOrWhiteSpace($ResultText)) {
            Write-Host $ResultText -ForegroundColor Red
        }

        throw "AWS CLI failed during: $Operation"
    }

    return $ResultText
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI is not installed or is not available in PATH."
}

if ([string]::IsNullOrWhiteSpace($StateFile)) {
    $Pointer = Join-Path $PSScriptRoot "latest-state.txt"

    if (Test-Path $Pointer) {
        $StateFile = (Get-Content $Pointer -Raw).Trim()
    }
    else {
        $NewestState = Get-ChildItem `
            -Path $PSScriptRoot `
            -Filter "emr-resource-state-*.json" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($NewestState) {
            $StateFile = $NewestState.FullName
        }
    }
}

if (
    [string]::IsNullOrWhiteSpace($StateFile) -or
    -not (Test-Path $StateFile)
) {
    throw "State file not found. Supply -StateFile with the generated JSON file."
}

$State = Get-Content $StateFile -Raw | ConvertFrom-Json
$Region = $State.Region

Write-Host "State file: $StateFile"
Write-Host "Project   : $($State.Project)"
Write-Host "Region    : $Region"

$Confirmation = Read-Host "Type DELETE to remove this project's S3, IAM, and VPC resources"

if ($Confirmation -ne "DELETE") {
    Write-Host "Cleanup cancelled."
    exit 0
}

# ===================================================================
# TERMINATE CLUSTER
# ===================================================================
if ($State.ClusterId) {
    Write-Step "STEP 1 - Ensure the EMR cluster is terminated"

    $ClusterState = (
        Invoke-Aws `
            -AwsArgs @(
                "emr", "describe-cluster",
                "--cluster-id", $State.ClusterId,
                "--region", $Region,
                "--query", "Cluster.Status.State",
                "--output", "text"
            ) `
            -Operation "checking cluster" `
            -AllowFailure
    ).Trim()

    if (
        $ClusterState -and
        $ClusterState -notin @(
            "TERMINATED",
            "TERMINATED_WITH_ERRORS"
        )
    ) {
        Invoke-Aws `
            -AwsArgs @(
                "emr", "terminate-clusters",
                "--cluster-ids", $State.ClusterId,
                "--region", $Region
            ) `
            -Operation "terminating cluster" | Out-Null

        Invoke-Aws `
            -AwsArgs @(
                "emr", "wait", "cluster-terminated",
                "--cluster-id", $State.ClusterId,
                "--region", $Region
            ) `
            -Operation "waiting for cluster termination" | Out-Null
    }

    Write-Host "Cluster is terminated."
}

# Give EMR-created network interfaces time to disappear.
Write-Host "Waiting 20 seconds for EMR network cleanup..."
Start-Sleep -Seconds 20

# ===================================================================
# S3
# ===================================================================
if ($State.Bucket) {
    Write-Step "STEP 2 - Empty and delete the S3 bucket"

    Invoke-Aws `
        -AwsArgs @(
            "s3", "rm",
            "s3://$($State.Bucket)",
            "--recursive",
            "--region", $Region
        ) `
        -Operation "emptying S3 bucket" `
        -AllowFailure `
        -ShowOutput | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "s3api", "delete-bucket",
            "--bucket", $State.Bucket,
            "--region", $Region
        ) `
        -Operation "deleting S3 bucket" `
        -AllowFailure | Out-Null
}

# ===================================================================
# IAM
# ===================================================================
Write-Step "STEP 3 - Delete IAM policies, profile, and roles"

if ($State.Ec2RoleName) {
    Invoke-Aws `
        -AwsArgs @(
            "iam", "delete-role-policy",
            "--role-name", $State.Ec2RoleName,
            "--policy-name", $State.Ec2S3PolicyName
        ) `
        -Operation "deleting EC2 S3 inline policy" `
        -AllowFailure | Out-Null
}

if ($State.ServiceRoleName) {
    Invoke-Aws `
        -AwsArgs @(
            "iam", "delete-role-policy",
            "--role-name", $State.ServiceRoleName,
            "--policy-name", $State.ServicePassRolePolicyName
        ) `
        -Operation "deleting service PassRole inline policy" `
        -AllowFailure | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "iam", "detach-role-policy",
            "--role-name", $State.ServiceRoleName,
            "--policy-arn", "arn:aws:iam::aws:policy/service-role/AmazonEMRServicePolicy_v2"
        ) `
        -Operation "detaching AmazonEMRServicePolicy_v2" `
        -AllowFailure | Out-Null
}

if ($State.InstanceProfileName -and $State.Ec2RoleName) {
    Invoke-Aws `
        -AwsArgs @(
            "iam", "remove-role-from-instance-profile",
            "--instance-profile-name", $State.InstanceProfileName,
            "--role-name", $State.Ec2RoleName
        ) `
        -Operation "removing role from instance profile" `
        -AllowFailure | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "iam", "delete-instance-profile",
            "--instance-profile-name", $State.InstanceProfileName
        ) `
        -Operation "deleting instance profile" `
        -AllowFailure | Out-Null
}

if ($State.Ec2RoleName) {
    Invoke-Aws `
        -AwsArgs @(
            "iam", "delete-role",
            "--role-name", $State.Ec2RoleName
        ) `
        -Operation "deleting EC2 role" `
        -AllowFailure | Out-Null
}

if ($State.ServiceRoleName) {
    Invoke-Aws `
        -AwsArgs @(
            "iam", "delete-role",
            "--role-name", $State.ServiceRoleName
        ) `
        -Operation "deleting EMR service role" `
        -AllowFailure | Out-Null
}

# ===================================================================
# EMR-CREATED SECURITY GROUPS AND ENIS
# ===================================================================
if ($State.VpcId) {
    Write-Step "STEP 4 - Delete EMR-created security groups"

    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {
        $NetworkInterfaces = (
            Invoke-Aws `
                -AwsArgs @(
                    "ec2", "describe-network-interfaces",
                    "--filters", "Name=vpc-id,Values=$($State.VpcId)",
                    "--region", $Region,
                    "--query", "NetworkInterfaces[?Status=='available'].NetworkInterfaceId",
                    "--output", "text"
                ) `
                -Operation "listing available network interfaces" `
                -AllowFailure
        ).Trim()

        if ($NetworkInterfaces) {
            foreach ($Eni in ($NetworkInterfaces -split "\s+")) {
                if ($Eni) {
                    Invoke-Aws `
                        -AwsArgs @(
                            "ec2", "delete-network-interface",
                            "--network-interface-id", $Eni,
                            "--region", $Region
                        ) `
                        -Operation "deleting network interface $Eni" `
                        -AllowFailure | Out-Null
                }
            }
        }

        $SecurityGroups = (
            Invoke-Aws `
                -AwsArgs @(
                    "ec2", "describe-security-groups",
                    "--filters", "Name=vpc-id,Values=$($State.VpcId)",
                    "--region", $Region,
                    "--query", "SecurityGroups[?GroupName!='default'].GroupId",
                    "--output", "text"
                ) `
                -Operation "listing security groups" `
                -AllowFailure
        ).Trim()

        if (-not $SecurityGroups) {
            break
        }

        foreach ($GroupId in ($SecurityGroups -split "\s+")) {
            if ($GroupId) {
                Invoke-Aws `
                    -AwsArgs @(
                        "ec2", "delete-security-group",
                        "--group-id", $GroupId,
                        "--region", $Region
                    ) `
                    -Operation "deleting security group $GroupId" `
                    -AllowFailure | Out-Null
            }
        }

        Start-Sleep -Seconds 10
    }
}

# ===================================================================
# ROUTING, SUBNET, IGW, VPC
# ===================================================================
Write-Step "STEP 5 - Delete route table, subnet, Internet Gateway, and VPC"

if ($State.RouteAssociationId) {
    Invoke-Aws `
        -AwsArgs @(
            "ec2", "disassociate-route-table",
            "--association-id", $State.RouteAssociationId,
            "--region", $Region
        ) `
        -Operation "disassociating route table" `
        -AllowFailure | Out-Null
}

if ($State.RouteTableId) {
    Invoke-Aws `
        -AwsArgs @(
            "ec2", "delete-route-table",
            "--route-table-id", $State.RouteTableId,
            "--region", $Region
        ) `
        -Operation "deleting route table" `
        -AllowFailure | Out-Null
}

if ($State.SubnetId) {
    Invoke-Aws `
        -AwsArgs @(
            "ec2", "delete-subnet",
            "--subnet-id", $State.SubnetId,
            "--region", $Region
        ) `
        -Operation "deleting subnet" `
        -AllowFailure | Out-Null
}

if ($State.InternetGatewayId -and $State.VpcId) {
    Invoke-Aws `
        -AwsArgs @(
            "ec2", "detach-internet-gateway",
            "--internet-gateway-id", $State.InternetGatewayId,
            "--vpc-id", $State.VpcId,
            "--region", $Region
        ) `
        -Operation "detaching Internet Gateway" `
        -AllowFailure | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "delete-internet-gateway",
            "--internet-gateway-id", $State.InternetGatewayId,
            "--region", $Region
        ) `
        -Operation "deleting Internet Gateway" `
        -AllowFailure | Out-Null
}

if ($State.VpcId) {
    Invoke-Aws `
        -AwsArgs @(
            "ec2", "delete-vpc",
            "--vpc-id", $State.VpcId,
            "--region", $Region
        ) `
        -Operation "deleting VPC" `
        -AllowFailure | Out-Null
}

Write-Step "CLEANUP FINISHED"

Write-Host "Review the AWS Console to confirm that the dedicated VPC and bucket are gone."
Write-Host "The local state, logs, generated JSON, and downloaded output were not deleted."
