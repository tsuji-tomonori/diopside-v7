import assert from 'node:assert/strict';
import test from 'node:test';

import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';

import { DiopsideStack } from '../lib/diopside-stack.js';

function template(): Template {
  const app = new cdk.App();
  return Template.fromStack(new DiopsideStack(app, 'TestStack'));
}

// serverlessな暗号化storageとqueueだけを使用することを検証する。
test('serverlessな暗号化storageとqueueを使用する', () => {
  const value = template();
  value.resourceCountIs('AWS::S3::Bucket', 5);
  value.resourceCountIs('AWS::DynamoDB::Table', 1);
  value.resourceCountIs('AWS::SQS::Queue', 3);
  value.hasResourceProperties('AWS::DynamoDB::Table', {
    BillingMode: 'PAY_PER_REQUEST',
    PointInTimeRecoverySpecification: { PointInTimeRecoveryEnabled: true },
  });
  value.hasResourceProperties('AWS::S3::Bucket', {
    BucketEncryption: Match.objectLike({
      ServerSideEncryptionConfiguration: Match.arrayWith([
        Match.objectLike({ ServerSideEncryptionByDefault: { SSEAlgorithm: 'AES256' } }),
      ]),
    }),
    VersioningConfiguration: { Status: 'Enabled' },
  });
});

// 実行roleを分離し、短時間batchを予定することを検証する。
test('実行roleを分離して短時間batchを予定する', () => {
  const value = template();
  value.resourceCountIs('AWS::IAM::Role', 4);
  value.resourceCountIs('AWS::Lambda::Function', 3);
  value.resourceCountIs('AWS::Events::Rule', 5);
  value.resourceCountIs('AWS::Lambda::EventSourceMapping', 2);
  value.hasResourceProperties('AWS::Lambda::Function', {
    Timeout: 900,
    ReservedConcurrentExecutions: 2,
    TracingConfig: { Mode: 'Active' },
  });
});

// 固定費のあるnetwork・database resourceを作成しないことを検証する。
test('固定費のあるnetwork・database resourceを作成しない', () => {
  const resources = template().toJSON().Resources as Record<string, { Type: string }>;
  const forbidden = new Set([
    'AWS::EC2::NatGateway',
    'AWS::EC2::Instance',
    'AWS::RDS::DBInstance',
    'AWS::OpenSearchService::Domain',
  ]);
  assert.deepEqual(
    Object.values(resources).filter((resource) => forbidden.has(resource.Type)),
    [],
  );
});

// 非公開S3をsecurity header付きCloudFront経由で配信することを検証する。
test('非公開S3をsecurity header付きCloudFront経由で配信する', () => {
  const value = template();
  value.resourceCountIs('AWS::CloudFront::Distribution', 1);
  value.hasResourceProperties('AWS::CloudFront::ResponseHeadersPolicy', {
    ResponseHeadersPolicyConfig: {
      SecurityHeadersConfig: Match.objectLike({
        ContentTypeOptions: { Override: true },
        FrameOptions: { FrameOption: 'DENY', Override: true },
      }),
    },
  });
});
