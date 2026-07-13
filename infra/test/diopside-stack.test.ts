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
  // 1. 初期化
  const expectedBuckets = 5;

  // 2. テストの実行
  const value = template();

  // 3. アサーション
  value.resourceCountIs('AWS::S3::Bucket', expectedBuckets);
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
  // 1. 初期化
  const expectedRoles = 4;

  // 2. テストの実行
  const value = template();

  // 3. アサーション
  value.resourceCountIs('AWS::IAM::Role', expectedRoles);
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
  // 1. 初期化
  const forbidden = new Set([
    'AWS::EC2::NatGateway',
    'AWS::EC2::Instance',
    'AWS::RDS::DBInstance',
    'AWS::OpenSearchService::Domain',
  ]);

  // 2. テストの実行
  const resources = template().toJSON().Resources as Record<string, { Type: string }>;
  const forbiddenResources = Object.values(resources).filter((resource) => forbidden.has(resource.Type));

  // 3. アサーション
  assert.deepEqual(
    forbiddenResources,
    [],
  );
});

// 非公開S3をsecurity header付きCloudFront経由で配信することを検証する。
test('非公開S3をsecurity header付きCloudFront経由で配信する', () => {
  // 1. 初期化
  const expectedDistributions = 1;

  // 2. テストの実行
  const value = template();

  // 3. アサーション
  value.resourceCountIs('AWS::CloudFront::Distribution', expectedDistributions);
  value.hasResourceProperties('AWS::CloudFront::ResponseHeadersPolicy', {
    ResponseHeadersPolicyConfig: {
      SecurityHeadersConfig: Match.objectLike({
        ContentTypeOptions: { Override: true },
        FrameOptions: { FrameOption: 'DENY', Override: true },
      }),
    },
  });
});
