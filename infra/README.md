# Infrastructure (AWS)

CloudFormation for running uwr-training on AWS, deployed **from GitHub Actions only** —
never from a laptop. It's a **single stack** that we build up incrementally; right now it
provisions just the database. Compute and the rest get added to the same stack later.

| File | What it is |
| --- | --- |
| `stack.yaml` | The app's CloudFormation stack. So far: an RDS PostgreSQL 16 instance sized for the AWS Free Tier (`db.t4g.micro`, 20 GB gp2, Single-AZ). |

## Set up the deploy user (one-time, manual)

The GitHub Actions workflow authenticates as an IAM user with a scoped policy. Create
it once in the AWS console (or CLI) of the account you're deploying to. Everything
below is done by **you**, by hand — the templates never create this user (a stack
shouldn't be able to grant itself more power than it already has).

### 1. Create the policy

- IAM → **Policies** → **Create policy** → **JSON** tab.
- Paste the policy below.
- Name it `uwr-training-deploy`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormation",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ListStackResources",
        "cloudformation:ListStacks",
        "cloudformation:GetTemplate",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:ListChangeSets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RdsProvisioning",
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBInstance",
        "rds:ModifyDBInstance",
        "rds:DeleteDBInstance",
        "rds:DescribeDBInstances",
        "rds:CreateDBSubnetGroup",
        "rds:ModifyDBSubnetGroup",
        "rds:DeleteDBSubnetGroup",
        "rds:DescribeDBSubnetGroups",
        "rds:CreateDBSnapshot",
        "rds:DescribeDBSnapshots",
        "rds:AddTagsToResource",
        "rds:RemoveTagsFromResource",
        "rds:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Ec2SecurityGroupAndVpc",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeRouteTables",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateVpcEndpoint",
        "ec2:DeleteVpcEndpoints",
        "ec2:ModifyVpcEndpoint",
        "ec2:DescribeVpcEndpoints",
        "ec2:DescribePrefixLists"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EcrAuthToken",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "EcrManageProjectRepo",
      "Effect": "Allow",
      "Action": "ecr:*",
      "Resource": "arn:aws:ecr:*:*:repository/uwr-training-*"
    },
    {
      "Sid": "S3ManageProjectBuckets",
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::uwr-training-*",
        "arn:aws:s3:::uwr-training-*/*"
      ]
    },
    {
      "Sid": "LambdaAndApiGateway",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListVersionsByFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:GetPolicy",
        "lambda:TagResource",
        "lambda:UntagResource",
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:PATCH",
        "apigateway:DELETE"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy",
        "logs:TagResource",
        "logs:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IamForLambdaExecutionRole",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:TagRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/uwr-training-*"
    }
  ]
}
```

What it allows, and why:

- **CloudFormation** — create/update/delete the stack and use change sets.
- **RDS** — create/modify/delete the DB instance and subnet group, take snapshots
  (the template's `DeletionPolicy: Snapshot`), and tag resources.
- **EC2 (security groups, VPC read, VPC endpoint)** — create the DB + Lambda security
  groups, read the VPC/subnets/route tables, and create the S3 gateway endpoint that lets
  the VPC Lambda reach S3 without a (paid) NAT gateway. No instance creation is granted.
- **ECR** — `GetAuthorizationToken` (account-level, must be `Resource: "*"`) plus full
  management (`ecr:*`) of **this project's repos only** (`repository/uwr-training-*`).
  It's `ecr:*` rather than an action list because CloudFormation calls a shifting set of
  repo APIs across create/update (lifecycle policy, repo policy, tag mutability, …) —
  scoping by *resource* to the project's repos avoids chasing each one, without granting
  access to any other repository.
- **S3** — full management (`s3:*`) of **this project's buckets only**
  (`uwr-training-*`), same resource-scoped reasoning as ECR (CloudFormation touches many
  `PutBucket*` config APIs). Bounded to the project prefix — no access to any other
  bucket in the account.
- **Lambda + API Gateway** — create/update the API function and its HTTP API.
- **CloudWatch Logs** — create the function's log group with a retention policy.
- **IAM** — create/pass the Lambda's execution role and manage its inline policy (the
  role's S3 access). This is the one privileged addition: it's **scoped to
  `role/uwr-training-*`** so the deploy user can only manage roles for this project, not
  arbitrary ones — it can't grant itself broader access.

Most actions use `Resource: "*"` because CloudFormation names resources with generated
identifiers not known ahead of time, and many of these tag/describe APIs don't support
resource-level scoping cleanly. The sensitive exception — `iam:*` — **is** ARN-scoped to
this project's role prefix. Everything else is bounded by **action**: no S3 data access,
no arbitrary IAM, etc. Tighten further to specific ARNs later if you want.

### 2. Create the user

- IAM → **Users** → **Create user**, e.g. `uwr-training-ci`.
- **Do not** enable console access — this identity is for automation only.
- Attach the `uwr-training-deploy` policy directly (permissions → attach policies).

### 3. Create an access key

- Open the user → **Security credentials** → **Create access key**.
- Use case: **Application running outside AWS** (or **Third-party service**).
- Copy the **Access key ID** and **Secret access key** now — the secret is shown once.

> **Better, if you can:** skip static keys and use GitHub's OIDC federation instead —
> add an IAM **OIDC identity provider** for `token.actions.githubusercontent.com` and a
> role that trusts your repo, attaching the same policy. GitHub Actions then assumes the
> role with no long-lived secret to leak or rotate. Static keys (above) are the simplest
> path; note it here so we can switch later.

### 4. Store the credentials in GitHub

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` — region to deploy into.
- `DB_MASTER_PASSWORD` — RDS master password; passed to the template as a `NoEcho`
  parameter (never committed). 8–128 chars, and (RDS restriction) no `/`, `@`, `"`, or
  spaces.
- `DB_ALLOWED_CIDR` *(optional)* — CIDR allowed to reach Postgres (e.g. your IP,
  `203.0.113.4/32`). Omit and it defaults to a non-routable placeholder so nothing is
  exposed. **Never `0.0.0.0/0`.**

For the **API Lambda** (used once the API deploy runs — see below):

- `APP_SECRET_KEY` — signs session-cookie JWTs (`NoEcho`). Generate once and keep stable
  so existing sessions survive redeploys.

(No S3 or CORS secrets yet — media isn't wired up, and CORS will come from the in-stack
front-end's URL once that's added. See the parameters note in `stack.yaml`.)

## Deploying

Two **manual** workflows (Actions tab → *Run workflow*), both targeting the same stack:

**`deploy-infra.yml`** — the DB/ECR/networking side. Configures credentials, discovers
the default VPC + subnets (no IDs hand-entered), reads the currently-live `ApiImageUri`
so it isn't reset, and runs `aws cloudformation deploy` (idempotent;
`--no-fail-on-empty-changeset`). Run it for the initial bootstrap and whenever the
template's DB/networking changes.

**`deploy-api.yml`** — the API side. Reads the ECR repo from the stack, builds
`docker/dockerfiles/lambda.Dockerfile`, pushes it, then deploys with `ApiImageUri` set to
the pushed **digest** (immutable — CloudFormation reliably sees the change). Run it to
ship API code changes. Prints the API URL to test.

Both share a `concurrency` group so they can't run at once (they mutate the same stack).

> **Why both pass every parameter:** `aws cloudformation deploy` resets any parameter you
> omit back to its template default. So each workflow passes the full set — `deploy-api`
> owns `ApiImageUri`; `deploy-infra` preserves it by reading the live value. `NoEcho`
> params (`MasterUserPassword`, `SecretKey`) can't be read back, so they always come from
> secrets in both.

### First-time order

1. Set the secrets above (at minimum the AWS creds, `AWS_REGION`, `DB_MASTER_PASSWORD`;
   add `APP_SECRET_KEY` before the API deploy).
2. Run **Deploy infrastructure** — bootstraps the DB + ECR repo (no image yet).
3. Run **Migrate database** — creates the schema (see below).
4. Run **Deploy API** — builds/pushes the image and brings up the Lambda + HTTP API.

## Migrations

The `.github/workflows/migrate-db.yml` workflow runs Alembic against the RDS database
(`app.cli migrate`, which only upgrades when the DB isn't already at head) — **manual
only**, run it after a deploy that includes new revisions.

It reads the **host/port/name from the stack outputs** (no secret needed) and the
**password from the `DB_MASTER_PASSWORD` secret** — the master password is a `NoEcho`
CloudFormation parameter and can't be read back via the API, so it lives only in that
secret. (Username defaults to `uwr`, overridable via an optional `DB_MASTER_USERNAME`
secret.)

**Runner access to the DB:** GitHub-hosted runners have unpredictable public IPs from a
large AWS range, so we can't pre-allow them in the security group. The job detects its
own egress IP, opens the SG to just that `/32` on 5432 for the run, then revokes it in an
`always()` step (so it's torn down even if the migration fails). The DB stays closed the
rest of the time. This needs only the `ec2:Authorize/RevokeSecurityGroupIngress` +
`cloudformation:DescribeStacks` actions already in the policy above.

> Assumes the RDS default parameter group (`rds.force_ssl=0`), so a plain connection
> works. If you later set `force_ssl=1`, the migration URL will need an SSL option.

## `stack.yaml` parameters (set at deploy time)

The workflow fills these in; you don't set them by hand.

| Parameter | Notes |
| --- | --- |
| `VpcId` | Auto-resolved by the workflow to the account's **default VPC** (free; avoids NAT charges). |
| `SubnetIds` | Auto-resolved to the default VPC's subnets — one per AZ, satisfying RDS's two-AZ requirement. |
| `MasterUserPassword` | From the `DB_MASTER_PASSWORD` secret; `NoEcho`. |
| `AllowedCidr` | From the optional `DB_ALLOWED_CIDR` secret; defaults to a non-routable placeholder. **Never `0.0.0.0/0`.** |
| `PubliclyAccessible` | `true` for now so migrations run from the CI runner; the Lambda reaches the DB privately regardless. Flip to `false` later to fully close it. |
| `InstanceClass` | `db.t4g.micro` (default, cheapest Free-Tier). `db.t3.micro` fallback if t4g is unavailable in your region. |
| `DeletionProtection` | `false` while experimenting; `true` for anything real. |
| `ApiImageUri` | ECR image the API Lambda runs. **Empty on the first deploy** (creates ECR + DB only); set by the API deploy after an image is pushed, which brings up the Lambda + HTTP API. |
| `SecretKey` | API Lambda's JWT signing key, from the `APP_SECRET_KEY` secret. Only needed once `ApiImageUri` is set. |

## The API is a two-phase deploy (chicken-and-egg)

The Lambda needs an image, but the ECR repo to push the image to lives in the same
stack. So the API comes up in two passes:

1. **Bootstrap** — deploy with `ApiImageUri` empty. The `HasImage` condition skips the
   Lambda/HTTP API but creates the **ECR repo** (and the DB). This is what the current
   `deploy-infra.yml` does.
2. **API deploy** (`deploy-api.yml`) — builds the image
   (`docker/dockerfiles/lambda.Dockerfile`), pushes it to that repo, then deploys again
   with `ApiImageUri` set to the pushed digest. That brings up the Lambda, its
   role/log group, the DB ingress rule, and the HTTP API.

## Notes before the first deploy

- **Free tier is account-based** (first 12 months, single instance). Confirm the target
  account still qualifies before relying on "free".
- **Region:** `db.t4g.micro` isn't offered in every region — the `db.t3.micro` fallback
  covers that.
- The stack builds the **database + API** (RDS, ECR, Lambda, HTTP API). The front-end
  stays on Render for now and moves to AWS in a later slice.
- **Cost:** stays in free tier. RDS/subnets/security groups are free; Lambda + HTTP API
  have generous free tiers (1M requests/mo). No NAT Gateway anywhere — that's the one
  thing that would bill.
- **VPC cost:** none. RDS and the Lambda are in the default VPC; a VPC/subnets/SGs are
  all free. (An S3 gateway endpoint — also free — gets added when media is wired up.)
- **Media/S3:** the media bucket now exists in the stack (`MediaBucketName` output), but
  the app isn't repointed at it yet — that's a follow-up (Lambda env + exec-role S3
  perms + S3 gateway endpoint + the `storage.py` credentials change). Until then media
  endpoints still won't work; everything else (auth, trainings, logs, tests) does. The
  order is: deploy the bucket → `aws s3 sync` old→new → reconnect the app.
