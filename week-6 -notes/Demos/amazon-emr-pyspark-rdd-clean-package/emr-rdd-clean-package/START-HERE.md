# Amazon EMR PySpark RDD Demo — Start Here

This folder contains only the files needed to create a fresh Amazon EMR environment, run the attached PySpark RDD job, download the result, and remove the AWS resources afterward.

## Mandatory files

| File | Purpose | Where it is used |
|---|---|---|
| `START-HERE.md` | Complete instructions | Open in VS Code, Notepad, or a browser that displays Markdown |
| `01-create-run-emr.ps1` | Creates AWS resources and runs the job | Windows PowerShell |
| `02-cleanup-all.ps1` | Deletes S3, IAM, and VPC resources created by the first script | Windows PowerShell |
| `06_rdd_aws_loading_saving_demo.py` | PySpark RDD application | Uploaded automatically to S3 and executed on EMR |
| `retail_orders.csv` | Input data | Uploaded automatically to S3 |

You do **not** need to manually create or maintain JSON policy files. The PowerShell script generates valid JSON files automatically in a temporary `.generated-<timestamp>` folder.

Do not copy the older experimental files into this clean folder:

- `emr-end-to-end.ps1`
- `emr-resume-after-json-fix.ps1`
- V2, V3, V4, or V5 resume scripts
- `ec2-attributes*.json`
- `instance-groups*.json`
- `spark-step*.json`
- trust-policy JSON files
- policy JSON files

---

# What the script creates

```text
Windows PowerShell
        |
        | AWS CLI
        v
New dedicated VPC
  |-- Internet Gateway
  |-- Public subnet
  |-- Public route table
  `-- EMR-created security groups

New IAM roles
  |-- EMR service role
  `-- EC2 role + instance profile

New private S3 bucket
  |-- rdd-demo/input/retail_orders.csv
  |-- rdd-demo/scripts/06_rdd_aws_loading_saving_demo.py
  |-- rdd-demo/output/run-<timestamp>/
  `-- rdd-demo/logs/

Amazon EMR 7.13.0
  |-- 1 Primary node
  |-- 1 Core node
  `-- Spark step using command-runner.jar and spark-submit
```

The script chooses the first offered instance type from:

```text
m5.xlarge
m6i.xlarge
m5.large
m6i.large
```

The cluster has a 15-minute idle auto-termination policy and is also terminated by the script after the job finishes.

---

# Part A — One-time setup in the AWS Console

## A1. Sign in

Use the AWS Console only for the initial IAM administrator setup and later for viewing the result.

Do not create or use root access keys.

## A2. Prepare one IAM administrator user

For a personal training account, use an IAM administrator such as:

```text
geethaiamadmin
```

In the AWS Console:

```text
IAM
→ Users
→ geethaiamadmin
→ Permissions
```

For this isolated training exercise, the user needs permissions to create and delete IAM, VPC, EC2, S3, and EMR resources. A temporary `AdministratorAccess` attachment is the simplest lab setup.

After the demonstration, replace broad access with least-privilege policies.

## A3. Create a fresh access key

In the AWS Console:

```text
IAM
→ Users
→ geethaiamadmin
→ Security credentials
→ Create access key
→ Command Line Interface
```

Store the access key securely.

Never paste an access key or secret key into chat, email, source code, or screenshots. Rotate any key that has been exposed.

---

# Part B — Install and configure AWS CLI in Windows PowerShell

All commands in this section are run in **Windows PowerShell**, not in the AWS Console and not in Python.

## B1. Open PowerShell

```text
Windows Start
→ Search for PowerShell
→ Open Windows PowerShell
```

## B2. Check AWS CLI

```powershell
aws --version
```

When AWS CLI is not installed, install AWS CLI v2 for Windows and reopen PowerShell.

Official installer:

```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

## B3. Configure a named profile

```powershell
aws configure --profile emr-admin
```

Enter:

```text
AWS Access Key ID:     your new IAM-user access key
AWS Secret Access Key: your new IAM-user secret
Default region name:   ap-south-1
Default output format: json
```

## B4. Activate the profile in the current PowerShell window

```powershell
$env:AWS_PROFILE = "emr-admin"
$env:AWS_REGION = "ap-south-1"
```

## B5. Confirm the identity

```powershell
aws sts get-caller-identity
```

Expected style:

```json
{
  "Account": "314993330933",
  "Arn": "arn:aws:iam::314993330933:user/geethaiamadmin"
}
```

Do not continue when the ARN ends in `:root`.

---

# Part C — Extract and verify the project files

## C1. Extract the ZIP

Example folder:

```text
C:\Personal\RevatureUSACTS\emr-rdd-clean-package
```

## C2. Open PowerShell in that folder

```powershell
cd "C:\Personal\RevatureUSACTS\emr-rdd-clean-package"
```

## C3. Confirm the five mandatory files

```powershell
Get-ChildItem
```

You must see:

```text
START-HERE.md
01-create-run-emr.ps1
02-cleanup-all.ps1
06_rdd_aws_loading_saving_demo.py
retail_orders.csv
```

---

# Part D — Run the complete EMR demonstration

## D1. Permit local scripts for this PowerShell session only

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

When prompted, type:

```text
Y
```

and press Enter.

This setting lasts only until the PowerShell window is closed.

## D2. Run the end-to-end script

```powershell
.\01-create-run-emr.ps1
```

Do not run the Python file directly. The PowerShell script uploads it to S3 and EMR runs it through `spark-submit`.

## D3. Expected major stages

```text
STEP 1  - Verify files and AWS identity
STEP 2  - Select an instance type and Availability Zone
STEP 3  - Create VPC
STEP 4  - Create Internet Gateway
STEP 5  - Create public subnet
STEP 6  - Create routing
STEP 7  - Create S3 bucket
STEP 8  - Create EMR service role
STEP 9  - Create EC2 role and instance profile
STEP 10 - Upload CSV and Python
STEP 11 - Generate cluster configuration
STEP 12 - Create EMR cluster
STEP 13 - Submit spark-submit
STEP 14 - Download output
FINAL SAFETY STEP - Terminate cluster
```

Creation and application execution commonly take several minutes.

Do not close PowerShell while the cluster is running.

## D4. Expected final output

```text
category,total_completed_revenue
Electronics,198540.00
Fashion,22420.00
Grocery,9074.00
```

The downloaded result is placed in a folder similar to:

```text
downloaded-output-20260717-193118
```

---

# Part E — Files generated automatically

The setup script creates these local files automatically:

```text
.generated-<timestamp>\
emr-resource-state-<timestamp>.json
latest-state.txt
emr-run-<timestamp>.log
downloaded-output-<timestamp>\
```

These are runtime files, not files you need to prepare manually.

The state JSON records:

```text
VPC ID
Subnet ID
Internet Gateway ID
Route table ID
S3 bucket
IAM roles
EMR cluster ID
Spark step ID
Output URI
```

The cleanup script reads this state file.

---

# Part F — View the result in the AWS Console

## F1. S3 result

Open:

```text
AWS Console
→ S3
→ Buckets
```

Search for the generated bucket. Its name starts with:

```text
geetha-emr-rdd-
```

Open:

```text
rdd-demo
→ output
→ run-<timestamp>
→ part-00000
```

`part-00000` contains the result.

`_SUCCESS` is an empty Spark success marker.

## F2. EMR cluster and Spark step

Open:

```text
AWS Console
→ Amazon EMR
→ EMR on EC2
→ Clusters
```

Region:

```text
Asia Pacific (Mumbai) — ap-south-1
```

The cluster will normally show `TERMINATED` because the script terminates it after completion.

Open the cluster, then open:

```text
Steps
```

The Spark step should show:

```text
COMPLETED
```

## F3. Logs

The logs remain in the generated S3 bucket:

```text
rdd-demo/logs/
```

---

# Part G — Remove all project AWS resources

Run cleanup only after reviewing the S3 output and EMR details.

In Windows PowerShell, from the same extracted folder:

```powershell
.\02-cleanup-all.ps1
```

The script reads:

```text
latest-state.txt
```

It asks:

```text
Type DELETE to remove this project's S3, IAM, and VPC resources
```

Type exactly:

```text
DELETE
```

The cleanup script removes:

```text
S3 objects and bucket
IAM inline policies
IAM managed policy attachment
Instance profile
EC2 role
EMR service role
EMR-created security groups
Public route table
Public subnet
Internet Gateway
VPC
```

The IAM administrator user and its CLI access key are not deleted.

---

# Common problems

## `AccessDenied`

Confirm the active profile:

```powershell
echo $env:AWS_PROFILE
aws sts get-caller-identity
```

The caller needs permission to create and delete the resources listed in this guide.

## Root ARN appears

Stop and configure the IAM administrator profile:

```powershell
$env:AWS_PROFILE = "emr-admin"
aws sts get-caller-identity
```

## Script execution is blocked

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Choose `Y`.

## A cluster remains active after an interruption

List active clusters:

```powershell
aws emr list-clusters --active --region ap-south-1 --output table
```

Terminate a cluster:

```powershell
aws emr terminate-clusters --cluster-ids j-XXXXXXXXXXXXX --region ap-south-1
```

Then run:

```powershell
.\02-cleanup-all.ps1
```

## Cleanup reports a VPC dependency

Wait one or two minutes for EMR network interfaces to disappear, then run the cleanup script again.

---

# Security and cost checklist

Before starting:

```text
[ ] IAM administrator profile is active
[ ] Caller ARN is not root
[ ] Access key has not been shared
[ ] Region is ap-south-1
[ ] All five files are present
```

After finishing:

```text
[ ] EMR cluster state is TERMINATED
[ ] Output was reviewed in S3
[ ] Cleanup script was run
[ ] Temporary AdministratorAccess will be reviewed or removed
[ ] Exposed access keys were rotated
```

---

# Official AWS references

- AWS CLI installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- EMR 7.13.0: https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-7130-release.html
- EMR service role: https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-iam-role.html
- EMR managed-policy tags: https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-iam-policies.html
- Add an EMR step with AWS CLI: https://docs.aws.amazon.com/emr/latest/ManagementGuide/add-step-cli.html
- Spark step: https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-submit-step.html
