import os
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_glue as glue,
)
from constructs import Construct

from . import data


class GlueCrawlerExperiment(Construct):

    def __init__(self, scope: Construct, construct_id: str, prefix: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, "InputJsonBucket")

        if prefix == 'json-data-example':
            sources = data.json_data_example()
        elif prefix == 'flat-and-one-common-key':
            sources = data.flat_and_one_common_key()
        else:
            sources = [s3_deploy.Source.asset(os.path.join(os.path.dirname(__file__), prefix))]

        s3_deploy.BucketDeployment(self,
                                   "InputJsonBucketDeployment",
                                   destination_bucket=bucket,
                                   destination_key_prefix=f"{prefix}/",
                                   sources=sources)

        role = iam.Role(
            self,
            "CrawlerRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
        )

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSGlueServiceRole"))
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=[f"{bucket.bucket_arn}/*"],
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            ))

        glue.CfnCrawler(
            self,
            "Crawler",
            role=role.role_name,
            targets=glue.CfnCrawler.TargetsProperty(s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://{bucket.bucket_name}/{prefix}/", )
            ], ),
            database_name=
            f"glue_crawler_experiment_{'_'.join(prefix.split('-'))}",
            tags={"glue-crawler-experiment": prefix},
        )


class GlueCrawlerExampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        GlueCrawlerExperiment(self, "DisjointKeys", "disjoint-keys")
        GlueCrawlerExperiment(self, "NonHiveDisjointKeys", "non-hive-disjoint-keys")
        GlueCrawlerExperiment(self, "OverlappingKeys", "overlapping-keys")
        GlueCrawlerExperiment(self, "JsonDataExample", "json-data-example")
        GlueCrawlerExperiment(self, "FlatAndOneCommonKey", "flat-and-one-common-key")
