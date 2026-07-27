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
      "Sid": "Ec2SecurityGroupAndVpcLookups",
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
        "ec2:CreateTags",
        "ec2:DeleteTags"
      ],
      "Resource": "*"
    }
  ]
}
```

What it allows, and why:

- **CloudFormation** — create/update/delete the stack and use change sets.
- **RDS** — create/modify/delete the DB instance and subnet group, take snapshots
  (the template's `DeletionPolicy: Snapshot`), and tag resources.
- **EC2 (security groups + VPC read)** — the template creates a security group and
  needs to read your VPC/subnets. No instance/network *creation* is granted.

Actions use `Resource: "*"` because CloudFormation creates resources with
CloudFormation-generated names that aren't known ahead of time, and RDS/EC2 tag and
security-group APIs don't all support resource-level scoping cleanly. It's still
scoped by **action** — this user can't touch IAM, S3, Lambda, etc. Tighten to specific
ARNs later if you want; it's not required to get going.

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

## Deploying

The `.github/workflows/deploy-infra.yml` workflow runs the deploy — **manual only**
(Actions tab → *Deploy infrastructure* → *Run workflow*). Infra changes shouldn't fire on
every push, and the DB is stateful. It:

1. Configures AWS credentials from the secrets above.
2. Validates the template.
3. Discovers the **default VPC + its subnets** with read-only EC2 calls, so no VPC/subnet
   IDs are ever hand-entered.
4. Runs `aws cloudformation deploy` against `infra/stack.yaml` (idempotent — safe to
   re-run; `--no-fail-on-empty-changeset` makes a no-op deploy succeed).
5. Prints the stack outputs (DB endpoint, port, name).

## `stack.yaml` parameters (set at deploy time)

The workflow fills these in; you don't set them by hand.

| Parameter | Notes |
| --- | --- |
| `VpcId` | Auto-resolved by the workflow to the account's **default VPC** (free; avoids NAT charges). |
| `SubnetIds` | Auto-resolved to the default VPC's subnets — one per AZ, satisfying RDS's two-AZ requirement. |
| `MasterUserPassword` | From the `DB_MASTER_PASSWORD` secret; `NoEcho`. |
| `AllowedCidr` | From the optional `DB_ALLOWED_CIDR` secret; defaults to a non-routable placeholder. **Never `0.0.0.0/0`.** |
| `PubliclyAccessible` | `true` for now so migrations can run before there's AWS compute; flip to `false` once the app runs inside the VPC. |
| `InstanceClass` | `db.t4g.micro` (default, cheapest Free-Tier). `db.t3.micro` fallback if t4g is unavailable in your region. |
| `DeletionProtection` | `false` while experimenting; `true` for anything real. |

## Notes before the first deploy

- **Free tier is account-based** (first 12 months, single instance). Confirm the target
  account still qualifies before relying on "free".
- **Region:** `db.t4g.micro` isn't offered in every region — the `db.t3.micro` fallback
  covers that.
- The stack currently builds only the **database**. Compute and networking get added to
  this same stack in later slices.
- **VPC cost:** none. RDS is always in a VPC, but a VPC/subnets/security groups are free
  — only a NAT Gateway bills, and this stack has none. Using the default VPC's public
  subnets keeps the DB reachable from your laptop (scoped by `AllowedCidr`) with no VPN.
