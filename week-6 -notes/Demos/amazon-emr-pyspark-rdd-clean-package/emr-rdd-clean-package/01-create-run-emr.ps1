#requires -Version 5.1
<#
01-create-run-emr.ps1

Creates a completely new Amazon EMR training environment:
- VPC
- Internet Gateway
- Public subnet and route table
- EMR service role
- EC2 role and instance profile
- Private S3 bucket
- EMR cluster
- Spark step

It uploads retail_orders.csv and 06_rdd_aws_loading_saving_demo.py,
runs spark-submit, downloads the output, and terminates the cluster.

Run this script from Windows PowerShell inside this project folder.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ===================================================================
# SETTINGS
# ===================================================================
$Region = "ap-south-1"
$ReleaseLabel = "emr-7.13.0"
$ProjectBase = "geetha-emr-rdd"
$Prefix = "rdd-demo"

$VpcCidr = "10.60.0.0/16"
$SubnetCidr = "10.60.1.0/24"

# The script tries these instance types in order and chooses the first
# one offered in an Availability Zone in the selected region.
$InstanceTypeCandidates = @(
    "m5.xlarge",
    "m6i.xlarge",
    "m5.large",
    "m6i.large"
)

$InputFile = Join-Path $PSScriptRoot "retail_orders.csv"
$SparkFile = Join-Path $PSScriptRoot "06_rdd_aws_loading_saving_demo.py"

$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$Project = "$ProjectBase-$Timestamp"
$GeneratedDirectory = Join-Path $PSScriptRoot ".generated-$Timestamp"
$StateFile = Join-Path $PSScriptRoot "emr-resource-state-$Timestamp.json"
$LatestStatePointer = Join-Path $PSScriptRoot "latest-state.txt"
$TranscriptFile = Join-Path $PSScriptRoot "emr-run-$Timestamp.log"

New-Item -ItemType Directory -Path $GeneratedDirectory -Force | Out-Null

# ===================================================================
# HELPERS
# ===================================================================
function Write-Step {
    param([Parameter(Mandatory=$true)][string]$Message)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-JsonAscii {
    param(
        [Parameter(Mandatory=$true)][object]$Object,
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$Depth = 30
    )

    $Json = ConvertTo-Json -InputObject $Object -Depth $Depth

    [System.IO.File]::WriteAllText(
        $Path,
        $Json,
        [System.Text.Encoding]::ASCII
    )
}

function Invoke-Aws {
    param(
        [Parameter(Mandatory=$true)][string[]]$AwsArgs,
        [Parameter(Mandatory=$true)][string]$Operation,
        [switch]$AllowFailure,
        [switch]$ShowOutput
    )

    # Windows PowerShell 5.1 may promote AWS CLI stderr to a
    # NativeCommandError. Temporarily use Continue and evaluate the
    # AWS CLI exit code ourselves.
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

function Save-State {
    Write-JsonAscii -Object $script:State -Path $StateFile
    [System.IO.File]::WriteAllText(
        $LatestStatePointer,
        $StateFile,
        [System.Text.Encoding]::ASCII
    )
}

function Test-RequiredFile {
    param([Parameter(Mandatory=$true)][string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Required file is missing: $Path"
    }
}

# ===================================================================
# STATE
# ===================================================================
$State = [ordered]@{
    CreatedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    Region = $Region
    ReleaseLabel = $ReleaseLabel
    Project = $Project
    Prefix = $Prefix
    AccountId = $null
    CallerArn = $null
    Bucket = $null
    VpcId = $null
    InternetGatewayId = $null
    SubnetId = $null
    RouteTableId = $null
    RouteAssociationId = $null
    ServiceRoleName = "$Project-service-role"
    Ec2RoleName = "$Project-ec2-role"
    InstanceProfileName = "$Project-ec2-role"
    Ec2S3PolicyName = "$Project-s3-access"
    ServicePassRolePolicyName = "$Project-pass-ec2-role"
    AvailabilityZone = $null
    InstanceType = $null
    ClusterId = $null
    ClusterState = $null
    StepId = $null
    StepState = $null
    InputUri = $null
    ScriptUri = $null
    OutputUri = $null
    LogUri = $null
    DownloadDirectory = $null
    Completed = $false
}
Save-State

$ClusterCreated = $false
$TranscriptStarted = $false

try {
    Start-Transcript -Path $TranscriptFile -Force | Out-Null
    $TranscriptStarted = $true

    # ===============================================================
    # PREFLIGHT
    # ===============================================================
    Write-Step "STEP 1 - Verify PowerShell files and AWS CLI identity"

    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        throw "AWS CLI is not installed or is not available in PATH."
    }

    Test-RequiredFile $InputFile
    Test-RequiredFile $SparkFile

    $IdentityJson = Invoke-Aws `
        -AwsArgs @(
            "sts", "get-caller-identity",
            "--region", $Region,
            "--output", "json"
        ) `
        -Operation "checking AWS identity"

    $Identity = $IdentityJson | ConvertFrom-Json
    $State.AccountId = $Identity.Account
    $State.CallerArn = $Identity.Arn
    Save-State

    Write-Host "Account: $($State.AccountId)"
    Write-Host "Caller : $($State.CallerArn)"
    Write-Host "Region : $Region"

    if ($State.CallerArn -match ":root$") {
        throw "Do not run this lab with root access keys. Configure an IAM administrator profile."
    }

    # Confirm that the selected EMR release is recognized.
    Invoke-Aws `
        -AwsArgs @(
            "emr", "describe-release-label",
            "--release-label", $ReleaseLabel,
            "--region", $Region,
            "--query", "ReleaseLabel",
            "--output", "text"
        ) `
        -Operation "validating EMR release label" | Out-Null

    # ===============================================================
    # INSTANCE TYPE AND AVAILABILITY ZONE
    # ===============================================================
    Write-Step "STEP 2 - Select an available EC2 instance type and Availability Zone"

    foreach ($Candidate in $InstanceTypeCandidates) {
        $CandidateAz = (
            Invoke-Aws `
                -AwsArgs @(
                    "ec2", "describe-instance-type-offerings",
                    "--location-type", "availability-zone",
                    "--filters", "Name=instance-type,Values=$Candidate",
                    "--region", $Region,
                    "--query", "InstanceTypeOfferings[0].Location",
                    "--output", "text"
                ) `
                -Operation "checking availability of $Candidate"
        ).Trim()

        if (
            -not [string]::IsNullOrWhiteSpace($CandidateAz) -and
            $CandidateAz -ne "None"
        ) {
            $State.InstanceType = $Candidate
            $State.AvailabilityZone = $CandidateAz
            break
        }
    }

    if (-not $State.InstanceType) {
        throw "None of the configured instance types is offered in $Region."
    }

    Save-State
    Write-Host "Instance type     : $($State.InstanceType)"
    Write-Host "Availability Zone : $($State.AvailabilityZone)"

    # ===============================================================
    # VPC
    # ===============================================================
    Write-Step "STEP 3 - Create a new VPC"

    $State.VpcId = (
        Invoke-Aws `
            -AwsArgs @(
                "ec2", "create-vpc",
                "--cidr-block", $VpcCidr,
                "--region", $Region,
                "--query", "Vpc.VpcId",
                "--output", "text"
            ) `
            -Operation "creating VPC"
    ).Trim()
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "wait", "vpc-available",
            "--vpc-ids", $State.VpcId,
            "--region", $Region
        ) `
        -Operation "waiting for VPC" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "create-tags",
            "--resources", $State.VpcId,
            "--tags",
            "Key=Name,Value=$Project-vpc",
            "Key=Project,Value=$Project",
            "Key=for-use-with-amazon-emr-managed-policies,Value=true",
            "--region", $Region
        ) `
        -Operation "tagging VPC" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "modify-vpc-attribute",
            "--vpc-id", $State.VpcId,
            "--enable-dns-support",
            "--region", $Region
        ) `
        -Operation "enabling VPC DNS support" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "modify-vpc-attribute",
            "--vpc-id", $State.VpcId,
            "--enable-dns-hostnames",
            "--region", $Region
        ) `
        -Operation "enabling VPC DNS hostnames" | Out-Null

    Write-Host "VPC ID: $($State.VpcId)"

    # ===============================================================
    # INTERNET GATEWAY
    # ===============================================================
    Write-Step "STEP 4 - Create and attach an Internet Gateway"

    $State.InternetGatewayId = (
        Invoke-Aws `
            -AwsArgs @(
                "ec2", "create-internet-gateway",
                "--region", $Region,
                "--query", "InternetGateway.InternetGatewayId",
                "--output", "text"
            ) `
            -Operation "creating Internet Gateway"
    ).Trim()
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "create-tags",
            "--resources", $State.InternetGatewayId,
            "--tags",
            "Key=Name,Value=$Project-igw",
            "Key=Project,Value=$Project",
            "--region", $Region
        ) `
        -Operation "tagging Internet Gateway" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "attach-internet-gateway",
            "--internet-gateway-id", $State.InternetGatewayId,
            "--vpc-id", $State.VpcId,
            "--region", $Region
        ) `
        -Operation "attaching Internet Gateway" | Out-Null

    Write-Host "Internet Gateway ID: $($State.InternetGatewayId)"

    # ===============================================================
    # PUBLIC SUBNET
    # ===============================================================
    Write-Step "STEP 5 - Create a public subnet"

    $State.SubnetId = (
        Invoke-Aws `
            -AwsArgs @(
                "ec2", "create-subnet",
                "--vpc-id", $State.VpcId,
                "--cidr-block", $SubnetCidr,
                "--availability-zone", $State.AvailabilityZone,
                "--region", $Region,
                "--query", "Subnet.SubnetId",
                "--output", "text"
            ) `
            -Operation "creating subnet"
    ).Trim()
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "create-tags",
            "--resources", $State.SubnetId,
            "--tags",
            "Key=Name,Value=$Project-public-subnet",
            "Key=Project,Value=$Project",
            "Key=for-use-with-amazon-emr-managed-policies,Value=true",
            "--region", $Region
        ) `
        -Operation "tagging subnet" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "modify-subnet-attribute",
            "--subnet-id", $State.SubnetId,
            "--map-public-ip-on-launch",
            "--region", $Region
        ) `
        -Operation "enabling public IPv4 assignment" | Out-Null

    Write-Host "Subnet ID: $($State.SubnetId)"

    # ===============================================================
    # ROUTE TABLE
    # ===============================================================
    Write-Step "STEP 6 - Create public routing"

    $State.RouteTableId = (
        Invoke-Aws `
            -AwsArgs @(
                "ec2", "create-route-table",
                "--vpc-id", $State.VpcId,
                "--region", $Region,
                "--query", "RouteTable.RouteTableId",
                "--output", "text"
            ) `
            -Operation "creating route table"
    ).Trim()
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "create-tags",
            "--resources", $State.RouteTableId,
            "--tags",
            "Key=Name,Value=$Project-public-route-table",
            "Key=Project,Value=$Project",
            "--region", $Region
        ) `
        -Operation "tagging route table" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "ec2", "create-route",
            "--route-table-id", $State.RouteTableId,
            "--destination-cidr-block", "0.0.0.0/0",
            "--gateway-id", $State.InternetGatewayId,
            "--region", $Region
        ) `
        -Operation "creating Internet route" | Out-Null

    $State.RouteAssociationId = (
        Invoke-Aws `
            -AwsArgs @(
                "ec2", "associate-route-table",
                "--route-table-id", $State.RouteTableId,
                "--subnet-id", $State.SubnetId,
                "--region", $Region,
                "--query", "AssociationId",
                "--output", "text"
            ) `
            -Operation "associating route table"
    ).Trim()
    Save-State

    Write-Host "Route table ID: $($State.RouteTableId)"

    # ===============================================================
    # S3 BUCKET
    # ===============================================================
    Write-Step "STEP 7 - Create a new private S3 bucket"

    $State.Bucket = "$ProjectBase-$($State.AccountId)-$Timestamp".ToLower()
    Save-State

    if ($Region -eq "us-east-1") {
        Invoke-Aws `
            -AwsArgs @(
                "s3api", "create-bucket",
                "--bucket", $State.Bucket,
                "--region", $Region
            ) `
            -Operation "creating S3 bucket" | Out-Null
    }
    else {
        Invoke-Aws `
            -AwsArgs @(
                "s3api", "create-bucket",
                "--bucket", $State.Bucket,
                "--region", $Region,
                "--create-bucket-configuration", "LocationConstraint=$Region"
            ) `
            -Operation "creating S3 bucket" | Out-Null
    }

    $PublicAccessPath = Join-Path $GeneratedDirectory "s3-public-access-block.json"

    Write-JsonAscii `
        -Path $PublicAccessPath `
        -Object @{
            BlockPublicAcls = $true
            IgnorePublicAcls = $true
            BlockPublicPolicy = $true
            RestrictPublicBuckets = $true
        }

    Invoke-Aws `
        -AwsArgs @(
            "s3api", "put-public-access-block",
            "--bucket", $State.Bucket,
            "--public-access-block-configuration", "file://$PublicAccessPath",
            "--region", $Region
        ) `
        -Operation "blocking public S3 access" | Out-Null

    Write-Host "Bucket: $($State.Bucket)"

    # ===============================================================
    # IAM ROLES AND POLICIES
    # ===============================================================
    Write-Step "STEP 8 - Create the EMR service role"

    $EmrTrustPath = Join-Path $GeneratedDirectory "emr-service-trust.json"

    Write-JsonAscii `
        -Path $EmrTrustPath `
        -Object @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Principal = @{
                        Service = "elasticmapreduce.amazonaws.com"
                    }
                    Action = "sts:AssumeRole"
                }
            )
        }

    Invoke-Aws `
        -AwsArgs @(
            "iam", "create-role",
            "--role-name", $State.ServiceRoleName,
            "--assume-role-policy-document", "file://$EmrTrustPath",
            "--description", "Amazon EMR service role for $Project"
        ) `
        -Operation "creating EMR service role" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "iam", "attach-role-policy",
            "--role-name", $State.ServiceRoleName,
            "--policy-arn", "arn:aws:iam::aws:policy/service-role/AmazonEMRServicePolicy_v2"
        ) `
        -Operation "attaching AmazonEMRServicePolicy_v2" | Out-Null

    Write-Step "STEP 9 - Create the EC2 role and instance profile"

    $Ec2TrustPath = Join-Path $GeneratedDirectory "emr-ec2-trust.json"

    Write-JsonAscii `
        -Path $Ec2TrustPath `
        -Object @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Principal = @{
                        Service = "ec2.amazonaws.com"
                    }
                    Action = "sts:AssumeRole"
                }
            )
        }

    Invoke-Aws `
        -AwsArgs @(
            "iam", "create-role",
            "--role-name", $State.Ec2RoleName,
            "--assume-role-policy-document", "file://$Ec2TrustPath",
            "--description", "EC2 role for Amazon EMR project $Project"
        ) `
        -Operation "creating EMR EC2 role" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "iam", "create-instance-profile",
            "--instance-profile-name", $State.InstanceProfileName
        ) `
        -Operation "creating instance profile" | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "iam", "add-role-to-instance-profile",
            "--instance-profile-name", $State.InstanceProfileName,
            "--role-name", $State.Ec2RoleName
        ) `
        -Operation "adding EC2 role to instance profile" | Out-Null

    # EC2 role: restricted access to this demo bucket.
    $Ec2S3PolicyPath = Join-Path $GeneratedDirectory "emr-ec2-s3-policy.json"

    Write-JsonAscii `
        -Path $Ec2S3PolicyPath `
        -Object @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Sid = "ListDemoPrefix"
                    Effect = "Allow"
                    Action = @(
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads"
                    )
                    Resource = "arn:aws:s3:::$($State.Bucket)"
                    Condition = @{
                        StringLike = @{
                            "s3:prefix" = @(
                                $Prefix,
                                "$Prefix/*"
                            )
                        }
                    }
                },
                @{
                    Sid = "ReadWriteDemoObjects"
                    Effect = "Allow"
                    Action = @(
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:AbortMultipartUpload",
                        "s3:ListMultipartUploadParts"
                    )
                    Resource = "arn:aws:s3:::$($State.Bucket)/$Prefix/*"
                }
            )
        }

    Invoke-Aws `
        -AwsArgs @(
            "iam", "put-role-policy",
            "--role-name", $State.Ec2RoleName,
            "--policy-name", $State.Ec2S3PolicyName,
            "--policy-document", "file://$Ec2S3PolicyPath"
        ) `
        -Operation "adding S3 access to EC2 role" | Out-Null

    # Custom EC2 role name: explicitly let the EMR service role pass it.
    $ServicePassRolePath = Join-Path $GeneratedDirectory "emr-service-pass-ec2-role.json"

    Write-JsonAscii `
        -Path $ServicePassRolePath `
        -Object @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Sid = "PassCustomEMREC2Role"
                    Effect = "Allow"
                    Action = "iam:PassRole"
                    Resource = "arn:aws:iam::$($State.AccountId):role/$($State.Ec2RoleName)"
                    Condition = @{
                        StringEquals = @{
                            "iam:PassedToService" = "ec2.amazonaws.com"
                        }
                    }
                }
            )
        }

    Invoke-Aws `
        -AwsArgs @(
            "iam", "put-role-policy",
            "--role-name", $State.ServiceRoleName,
            "--policy-name", $State.ServicePassRolePolicyName,
            "--policy-document", "file://$ServicePassRolePath"
        ) `
        -Operation "allowing the EMR service role to pass the EC2 role" | Out-Null

    Write-Host "Waiting 25 seconds for IAM propagation..."
    Start-Sleep -Seconds 25

    # ===============================================================
    # UPLOAD
    # ===============================================================
    Write-Step "STEP 10 - Upload the CSV and PySpark application"

    $State.InputUri = "s3://$($State.Bucket)/$Prefix/input/retail_orders.csv"
    $State.ScriptUri = "s3://$($State.Bucket)/$Prefix/scripts/06_rdd_aws_loading_saving_demo.py"
    $State.LogUri = "s3://$($State.Bucket)/$Prefix/logs/"
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "s3", "cp",
            $InputFile,
            $State.InputUri,
            "--region", $Region
        ) `
        -Operation "uploading retail_orders.csv" `
        -ShowOutput | Out-Null

    Invoke-Aws `
        -AwsArgs @(
            "s3", "cp",
            $SparkFile,
            $State.ScriptUri,
            "--region", $Region
        ) `
        -Operation "uploading PySpark application" `
        -ShowOutput | Out-Null

    # ===============================================================
    # EMR CLUSTER CONFIGURATION
    # ===============================================================
    Write-Step "STEP 11 - Generate and validate cluster configuration"

    $Ec2AttributesPath = Join-Path $GeneratedDirectory "ec2-attributes.json"
    $InstanceGroupsPath = Join-Path $GeneratedDirectory "instance-groups.json"
    $AutoTerminationPath = Join-Path $GeneratedDirectory "auto-termination.json"

    Write-JsonAscii `
        -Path $Ec2AttributesPath `
        -Object @{
            InstanceProfile = $State.InstanceProfileName
            SubnetId = $State.SubnetId
        }

    Write-JsonAscii `
        -Path $InstanceGroupsPath `
        -Object @(
            @{
                Name = "Primary"
                InstanceGroupType = "MASTER"
                InstanceType = $State.InstanceType
                InstanceCount = 1
                EbsConfiguration = @{
                    EbsBlockDeviceConfigs = @(
                        @{
                            VolumeSpecification = @{
                                VolumeType = "gp3"
                                SizeInGB = 32
                            }
                            VolumesPerInstance = 1
                        }
                    )
                    EbsOptimized = $true
                }
            },
            @{
                Name = "Core"
                InstanceGroupType = "CORE"
                InstanceType = $State.InstanceType
                InstanceCount = 1
                EbsConfiguration = @{
                    EbsBlockDeviceConfigs = @(
                        @{
                            VolumeSpecification = @{
                                VolumeType = "gp3"
                                SizeInGB = 32
                            }
                            VolumesPerInstance = 1
                        }
                    )
                    EbsOptimized = $true
                }
            }
        )

    Write-JsonAscii `
        -Path $AutoTerminationPath `
        -Object @{
            IdleTimeout = 900
        }

    $InstanceGroupJson = Get-Content $InstanceGroupsPath -Raw

    if ($InstanceGroupJson -match '"Market"') {
        throw "Generated instance-groups JSON contains unsupported Market property."
    }

    $InstanceGroupJson | ConvertFrom-Json | Out-Null
    Write-Host "Cluster JSON validated."

    # ===============================================================
    # CREATE CLUSTER
    # ===============================================================
    Write-Step "STEP 12 - Create the Amazon EMR cluster"

    $State.ClusterId = (
        Invoke-Aws `
            -AwsArgs @(
                "emr", "create-cluster",
                "--name", "$Project-cluster",
                "--release-label", $ReleaseLabel,
                "--applications", "Name=Hadoop", "Name=Spark",
                "--service-role", $State.ServiceRoleName,
                "--ec2-attributes", "file://$Ec2AttributesPath",
                "--instance-groups", "file://$InstanceGroupsPath",
                "--log-uri", $State.LogUri,
                "--scale-down-behavior", "TERMINATE_AT_TASK_COMPLETION",
                "--auto-termination-policy", "file://$AutoTerminationPath",
                "--unhealthy-node-replacement",
                "--tags",
                "for-use-with-amazon-emr-managed-policies=true",
                "Project=$Project",
                "--region", $Region,
                "--query", "ClusterId",
                "--output", "text"
            ) `
            -Operation "creating EMR cluster"
    ).Trim()

    $ClusterCreated = $true
    $State.ClusterState = "STARTING"
    Save-State

    Write-Host "Cluster ID: $($State.ClusterId)" -ForegroundColor Green
    Write-Host "Waiting for the cluster to become RUNNING..."

    Invoke-Aws `
        -AwsArgs @(
            "emr", "wait", "cluster-running",
            "--cluster-id", $State.ClusterId,
            "--region", $Region
        ) `
        -Operation "waiting for EMR cluster" | Out-Null

    $State.ClusterState = (
        Invoke-Aws `
            -AwsArgs @(
                "emr", "describe-cluster",
                "--cluster-id", $State.ClusterId,
                "--region", $Region,
                "--query", "Cluster.Status.State",
                "--output", "text"
            ) `
            -Operation "checking cluster state"
    ).Trim()
    Save-State

    Write-Host "Cluster state: $($State.ClusterState)" -ForegroundColor Green

    # ===============================================================
    # SPARK STEP
    # ===============================================================
    Write-Step "STEP 13 - Submit spark-submit as an EMR step"

    $RunId = Get-Date -Format "yyyyMMdd-HHmmss"
    $State.OutputUri = "s3://$($State.Bucket)/$Prefix/output/run-$RunId"
    Save-State

    $StepPath = Join-Path $GeneratedDirectory "spark-step.json"

    Write-JsonAscii `
        -Path $StepPath `
        -Object @(
            @{
                Name = "RDD loading and saving Spark job"
                ActionOnFailure = "CONTINUE"
                Type = "CUSTOM_JAR"
                Jar = "command-runner.jar"
                Args = @(
                    "spark-submit",
                    "--deploy-mode",
                    "cluster",
                    $State.ScriptUri,
                    "--input",
                    $State.InputUri,
                    "--output",
                    $State.OutputUri
                )
            }
        )

    $StepJson = Get-Content $StepPath -Raw

    if (-not $StepJson.TrimStart().StartsWith("[")) {
        throw "Spark step JSON must be an array and start with [."
    }

    $StepJson | ConvertFrom-Json | Out-Null
    Write-Host "Spark step JSON validated."

    $State.StepId = (
        Invoke-Aws `
            -AwsArgs @(
                "emr", "add-steps",
                "--cluster-id", $State.ClusterId,
                "--steps", "file://$StepPath",
                "--region", $Region,
                "--query", "StepIds[0]",
                "--output", "text"
            ) `
            -Operation "submitting Spark step"
    ).Trim()
    Save-State

    Write-Host "Step ID   : $($State.StepId)"
    Write-Host "Output URI: $($State.OutputUri)"
    Write-Host "Waiting for the Spark step to complete..."

    Invoke-Aws `
        -AwsArgs @(
            "emr", "wait", "step-complete",
            "--cluster-id", $State.ClusterId,
            "--step-id", $State.StepId,
            "--region", $Region
        ) `
        -Operation "waiting for Spark step" | Out-Null

    $State.StepState = (
        Invoke-Aws `
            -AwsArgs @(
                "emr", "describe-step",
                "--cluster-id", $State.ClusterId,
                "--step-id", $State.StepId,
                "--region", $Region,
                "--query", "Step.Status.State",
                "--output", "text"
            ) `
            -Operation "checking Spark step state"
    ).Trim()
    Save-State

    Write-Host "Step state: $($State.StepState)" -ForegroundColor Green

    if ($State.StepState -ne "COMPLETED") {
        throw "Spark step did not complete successfully."
    }

    # ===============================================================
    # DOWNLOAD RESULT
    # ===============================================================
    Write-Step "STEP 14 - List, download, and display the Spark output"

    Invoke-Aws `
        -AwsArgs @(
            "s3", "ls",
            "$($State.OutputUri)/",
            "--recursive",
            "--region", $Region
        ) `
        -Operation "listing Spark output" `
        -ShowOutput | Out-Null

    $State.DownloadDirectory = Join-Path $PSScriptRoot "downloaded-output-$RunId"
    New-Item -ItemType Directory -Path $State.DownloadDirectory -Force | Out-Null
    Save-State

    Invoke-Aws `
        -AwsArgs @(
            "s3", "cp",
            "$($State.OutputUri)/",
            "$($State.DownloadDirectory)\",
            "--recursive",
            "--exclude", "*",
            "--include", "part-*",
            "--region", $Region
        ) `
        -Operation "downloading Spark output" `
        -ShowOutput | Out-Null

    Write-Host ""
    Write-Host "FINAL OUTPUT" -ForegroundColor Yellow

    Get-ChildItem $State.DownloadDirectory -Filter "part-*" |
        ForEach-Object {
            Get-Content $_.FullName
        }

    $State.Completed = $true
    Save-State
}
catch {
    Write-Host ""
    Write-Host "RUN FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    if ($State.ClusterId) {
        Write-Host ""
        Write-Host "Cluster diagnostic information:" -ForegroundColor Yellow

        Invoke-Aws `
            -AwsArgs @(
                "emr", "describe-cluster",
                "--cluster-id", $State.ClusterId,
                "--region", $Region,
                "--query", "Cluster.Status",
                "--output", "json"
            ) `
            -Operation "reading failed cluster status" `
            -AllowFailure `
            -ShowOutput | Out-Null

        if ($State.StepId) {
            Invoke-Aws `
                -AwsArgs @(
                    "emr", "describe-step",
                    "--cluster-id", $State.ClusterId,
                    "--step-id", $State.StepId,
                    "--region", $Region,
                    "--query", "Step.Status",
                    "--output", "json"
                ) `
                -Operation "reading failed step status" `
                -AllowFailure `
                -ShowOutput | Out-Null
        }
    }

    Write-Host ""
    Write-Host "State file: $StateFile" -ForegroundColor Yellow
    Write-Host "Run 02-cleanup-all.ps1 after reviewing the error." -ForegroundColor Yellow

    throw
}
finally {
    if ($ClusterCreated -and $State.ClusterId) {
        Write-Step "FINAL SAFETY STEP - Terminate the EMR cluster"

        $CurrentState = (
            Invoke-Aws `
                -AwsArgs @(
                    "emr", "describe-cluster",
                    "--cluster-id", $State.ClusterId,
                    "--region", $Region,
                    "--query", "Cluster.Status.State",
                    "--output", "text"
                ) `
                -Operation "checking final cluster state" `
                -AllowFailure
        ).Trim()

        if (
            $CurrentState -and
            $CurrentState -notin @(
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
                -Operation "terminating EMR cluster" `
                -AllowFailure | Out-Null

            Invoke-Aws `
                -AwsArgs @(
                    "emr", "wait", "cluster-terminated",
                    "--cluster-id", $State.ClusterId,
                    "--region", $Region
                ) `
                -Operation "waiting for cluster termination" `
                -AllowFailure | Out-Null
        }

        $State.ClusterState = (
            Invoke-Aws `
                -AwsArgs @(
                    "emr", "describe-cluster",
                    "--cluster-id", $State.ClusterId,
                    "--region", $Region,
                    "--query", "Cluster.Status.State",
                    "--output", "text"
                ) `
                -Operation "recording final cluster state" `
                -AllowFailure
        ).Trim()

        Save-State
        Write-Host "Final cluster state: $($State.ClusterState)"
    }

    if ($TranscriptStarted) {
        Stop-Transcript | Out-Null
    }
}

Write-Step "COMPLETED"

Write-Host "Project       : $($State.Project)"
Write-Host "Bucket        : $($State.Bucket)"
Write-Host "Cluster ID    : $($State.ClusterId)"
Write-Host "Cluster state : $($State.ClusterState)"
Write-Host "Step ID       : $($State.StepId)"
Write-Host "Step state    : $($State.StepState)"
Write-Host "Output URI    : $($State.OutputUri)"
Write-Host "Local output  : $($State.DownloadDirectory)"
Write-Host "State file    : $StateFile"
Write-Host ""
Write-Host "The EMR cluster is terminated. S3, IAM, and VPC resources remain for review."
Write-Host "Run .\02-cleanup-all.ps1 when you are finished."
