"""InfiniteClaw — AWS CLI Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version

class AWSAdapter(DevOpsToolAdapter):
    name = "aws"
    display_name = "AWS CLI"
    icon = "☁️"
    category = "config_iac"
    default_port = 0
    description = "Amazon Web Services CLI integration"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "aws --version 2>/dev/null")
        if r["exit_code"] == 0:
            version = r["stdout"].split(" ")[0] if r["stdout"] else "unknown"
            
            # Check if credentials are valid via STS
            sts = self._exec(ssh, "aws sts get-caller-identity --output json 2>/dev/null")
            status = ToolStatus.RUNNING if sts["exit_code"] == 0 else ToolStatus.STOPPED
            extra_info = {"auth_status": "Valid credentials" if sts["exit_code"] == 0 else "Missing or invalid credentials"}
            
            return DetectionResult(status, version, 0, extra_info)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        ec2 = self._exec(ssh, "aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,PublicIpAddress]' --output json 2>/dev/null")
        s3 = self._exec(ssh, "aws s3 ls 2>/dev/null")
        rds = self._exec(ssh, "aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' --output json 2>/dev/null")
        
        return {
            "ec2_instances": ec2["stdout"][:2000] if ec2["exit_code"] == 0 else "N/A",
            "s3_buckets": s3["stdout"][:2000] if s3["exit_code"] == 0 else "N/A",
            "rds_instances": rds["stdout"][:1000] if rds["exit_code"] == 0 else "N/A"
        }

    def get_tool_schemas(self):
        return [
            {
                "type": "function", 
                "function": {
                    "name": "aws_ec2_instances", 
                    "description": "List EC2 instances in current region", 
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "aws_s3_list", 
                    "description": "List S3 buckets or contents. Use path for specific bucket (e.g. s3://my-bucket)", 
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "path": {"type": "string", "description": "Optional S3 path"}
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "aws_s3_sync", 
                    "description": "Sync files between local and S3 or between S3 buckets", 
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "source": {"type": "string", "description": "Source path (local or s3://)"},
                            "destination": {"type": "string", "description": "Destination path (local or s3://)"},
                            "delete": {"type": "boolean", "description": "If true, delete files in destination not in source"}
                        },
                        "required": ["source", "destination"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "aws_rds_status", 
                    "description": "Get status of RDS database instances", 
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "aws_route53_zones", 
                    "description": "List Route53 hosted zones", 
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "aws_ec2_instances":
            return self._exec(ssh, "aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,PublicIpAddress,PrivateIpAddress,KeyName]' --output table 2>&1")["stdout"]
        
        if fn == "aws_s3_list":
            path = args.get("path", "")
            cmd = f"aws s3 ls {path} 2>&1"
            return self._exec(ssh, cmd)["stdout"]
            
        if fn == "aws_s3_sync":
            del_flag = "--delete" if args.get("delete") else ""
            cmd = f"aws s3 sync {args['source']} {args['destination']} {del_flag} 2>&1"
            return self._exec(ssh, cmd, timeout=120)["stdout"]
            
        if fn == "aws_rds_status":
            return self._exec(ssh, "aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Engine,Endpoint.Address]' --output table 2>&1")["stdout"]
            
        if fn == "aws_route53_zones":
            return self._exec(ssh, "aws route53 list-hosted-zones --output table 2>&1")["stdout"]
            
        return f"Unknown function: {fn}"
