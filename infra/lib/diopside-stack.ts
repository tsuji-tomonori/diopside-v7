import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as eventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const backendDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../backend');

export class DiopsideStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const officialChannelId = new cdk.CfnParameter(this, 'OfficialChannelId', {
      type: 'String',
      description: 'Canonical YouTube channel ID to collect',
      allowedPattern: '^UC[A-Za-z0-9_-]{22}$',
    });
    const alertEmail = new cdk.CfnParameter(this, 'AlertEmail', {
      type: 'String',
      default: '',
      description: 'Optional operator email for alarm notifications',
    });
    const monthlyBudgetUsd = new cdk.CfnParameter(this, 'MonthlyBudgetUsd', {
      type: 'Number',
      default: 10,
      minValue: 1,
      description: 'Monthly AWS cost target in USD',
    });

    const accessLogs = new s3.Bucket(this, 'AccessLogs', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      lifecycleRules: [{ expiration: cdk.Duration.days(400) }],
      objectOwnership: s3.ObjectOwnership.OBJECT_WRITER,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    NagSuppressions.addResourceSuppressions(accessLogs, [
      {
        id: 'AwsSolutions-S1',
        reason: 'The dedicated access-log destination cannot recursively log to itself.',
      },
    ]);
    const raw = this.privateBucket('Raw', 30, accessLogs);
    const processed = this.privateBucket('Processed', 30, accessLogs);
    const configuration = this.privateBucket('Configuration', 90, accessLogs);
    const publicData = new s3.Bucket(this, 'PublicData', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      lifecycleRules: [{ noncurrentVersionExpiration: cdk.Duration.days(90) }],
      serverAccessLogsBucket: accessLogs,
      serverAccessLogsPrefix: 's3/public/',
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const control = new dynamodb.Table(this, 'ControlTable', {
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
      timeToLiveAttribute: 'expiresAt',
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    const youtubeApiKey = new secretsmanager.Secret(this, 'YouTubeApiKey', {
      description: 'YouTube Data API v3 key used by the collection runtime',
      generateSecretString: {
        passwordLength: 40,
        excludePunctuation: true,
      },
    });
    const pseudonymSecret = new secretsmanager.Secret(this, 'PseudonymSecret', {
      description: 'HMAC root secret for video-scoped public author pseudonyms',
      generateSecretString: { passwordLength: 64, excludePunctuation: true },
    });
    NagSuppressions.addResourceSuppressions(pseudonymSecret, [
      {
        id: 'AwsSolutions-SMG4',
        reason: 'Rotation would change stable video-scoped HMAC identities; replacement requires a versioned full reprocessing migration.',
      },
    ]);
    NagSuppressions.addResourceSuppressions(youtubeApiKey, [
      {
        id: 'AwsSolutions-SMG4',
        reason: 'Google API keys cannot be rotated by AWS; the operator runbook requires manual replacement and verification.',
      },
    ]);

    const deadLetterQueue = new sqs.Queue(this, 'JobDeadLetterQueue', {
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      enforceSSL: true,
      retentionPeriod: cdk.Duration.days(14),
    });
    const jobQueue = new sqs.Queue(this, 'JobQueue', {
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      enforceSSL: true,
      visibilityTimeout: cdk.Duration.minutes(15),
      deadLetterQueue: { queue: deadLetterQueue, maxReceiveCount: 4 },
    });
    const exportQueue = new sqs.Queue(this, 'ExportQueue', {
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      enforceSSL: true,
      visibilityTimeout: cdk.Duration.minutes(15),
      deadLetterQueue: { queue: deadLetterQueue, maxReceiveCount: 4 },
    });
    const alerts = new sns.Topic(this, 'OperationsAlerts', {
      enforceSSL: true,
      displayName: 'diopside operations alerts',
    });
    const hasAlertEmail = new cdk.CfnCondition(this, 'HasAlertEmail', {
      expression: cdk.Fn.conditionNot(cdk.Fn.conditionEquals(alertEmail.valueAsString, '')),
    });
    const subscription = new sns.CfnSubscription(this, 'AlertEmailSubscription', {
      protocol: 'email',
      endpoint: alertEmail.valueAsString,
      topicArn: alerts.topicArn,
    });
    subscription.cfnOptions.condition = hasAlertEmail;

    const collectorRole = this.runtimeRole('CollectorRole');
    const processorRole = this.runtimeRole('ProcessorRole');
    const exporterRole = this.runtimeRole('ExporterRole');
    const adminRole = new iam.Role(this, 'AdminRole', {
      assumedBy: new iam.AccountPrincipal(this.account),
      description: 'Operator role for audited job and compliance controls',
    });

    raw.grantReadWrite(collectorRole);
    configuration.grantRead(collectorRole);
    control.grantReadWriteData(collectorRole);
    jobQueue.grantSendMessages(collectorRole);

    raw.grantRead(processorRole);
    processed.grantReadWrite(processorRole);
    configuration.grantRead(processorRole);
    control.grantReadWriteData(processorRole);
    jobQueue.grantConsumeMessages(processorRole);
    jobQueue.grantSendMessages(processorRole);
    deadLetterQueue.grantSendMessages(processorRole);
    youtubeApiKey.grantRead(processorRole);
    pseudonymSecret.grantRead(processorRole);

    processed.grantRead(exporterRole);
    raw.grantDelete(exporterRole);
    processed.grantDelete(exporterRole);
    configuration.grantRead(exporterRole);
    publicData.grantReadWrite(exporterRole);
    control.grantReadWriteData(exporterRole);
    exportQueue.grantSendMessages(exporterRole);
    exportQueue.grantConsumeMessages(exporterRole);
    deadLetterQueue.grantSendMessages(exporterRole);

    control.grantReadWriteData(adminRole);
    raw.grantRead(adminRole);
    processed.grantRead(adminRole);
    processed.grantWrite(adminRole);
    publicData.grantRead(adminRole);
    configuration.grantRead(adminRole);
    jobQueue.grantSendMessages(adminRole);
    exportQueue.grantSendMessages(adminRole);
    deadLetterQueue.grantConsumeMessages(adminRole);
    adminRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:PutObject'],
      resources: [configuration.arnForObjects('gates/*')],
    }));
    adminRole.addToPolicy(new iam.PolicyStatement({
      actions: ['sqs:GetQueueAttributes'],
      resources: [deadLetterQueue.queueArn, jobQueue.queueArn, exportQueue.queueArn],
    }));
    adminRole.addToPolicy(new iam.PolicyStatement({
      actions: ['ce:GetCostAndUsage'],
      resources: ['*'],
    }));
    NagSuppressions.addResourceSuppressions(
      adminRole,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Read-only reports enumerate objects in named stack buckets; Cost Explorer does not support resource-level ARNs.',
        },
      ],
      true,
    );
    adminRole.addToPolicy(new iam.PolicyStatement({
      actions: ['sqs:StartMessageMoveTask', 'sqs:CancelMessageMoveTask', 'sqs:ListMessageMoveTasks'],
      resources: [deadLetterQueue.queueArn, jobQueue.queueArn, exportQueue.queueArn],
    }));

    const collector = this.worker('Collector', collectorRole, jobQueue.queueUrl);
    const processor = this.worker('Processor', processorRole, jobQueue.queueUrl);
    const exporter = this.worker('Exporter', exporterRole, jobQueue.queueUrl);
    processor.addEventSource(
      new eventSources.SqsEventSource(jobQueue, {
        batchSize: 10,
        reportBatchItemFailures: true,
      }),
    );
    exporter.addEventSource(
      new eventSources.SqsEventSource(exportQueue, {
        batchSize: 1,
        reportBatchItemFailures: true,
      }),
    );
    collector.addEnvironment('RAW_BUCKET', raw.bucketName);
    processor.addEnvironment('RAW_BUCKET', raw.bucketName);
    processor.addEnvironment('PROCESSED_BUCKET', processed.bucketName);
    processor.addEnvironment('CONFIGURATION_BUCKET', configuration.bucketName);
    processor.addEnvironment('YOUTUBE_API_KEY_SECRET_ARN', youtubeApiKey.secretArn);
    processor.addEnvironment('PSEUDONYM_SECRET_ARN', pseudonymSecret.secretArn);
    processor.addEnvironment('YOUTUBE_DAILY_QUOTA', '10000');
    exporter.addEnvironment('PUBLIC_BUCKET', publicData.bucketName);
    exporter.addEnvironment('PROCESSED_BUCKET', processed.bucketName);
    exporter.addEnvironment('RAW_BUCKET', raw.bucketName);
    exporter.addEnvironment('CONFIGURATION_BUCKET', configuration.bucketName);
    exporter.addEnvironment('EXPORT_QUEUE_URL', exportQueue.queueUrl);
    exporter.addEnvironment('JOB_HANDLER_STATIC_EXPORT', 'app.runtime.jobs:static_export');
    processorRole.addToPolicy(new iam.PolicyStatement({
      actions: ['cloudwatch:PutMetricData'],
      resources: ['*'],
      conditions: { StringEquals: { 'cloudwatch:namespace': 'Diopside' } },
    }));
    exporterRole.addToPolicy(new iam.PolicyStatement({
      actions: ['cloudwatch:PutMetricData'],
      resources: ['*'],
      conditions: { StringEquals: { 'cloudwatch:namespace': 'Diopside' } },
    }));
    for (const worker of [collector, processor, exporter]) {
      worker.addEnvironment('CONTROL_TABLE', control.tableName);
      worker.addEnvironment('DEAD_LETTER_QUEUE_URL', deadLetterQueue.queueUrl);
    }
    processor.addEnvironment('JOB_HANDLER_METADATA_SYNC', 'app.runtime.jobs:metadata_sync');
    processor.addEnvironment('JOB_HANDLER_COMMENT_COLLECT', 'app.runtime.jobs:comment_collect');
    processor.addEnvironment('JOB_HANDLER_LIVE_CHAT_COLLECT', 'app.runtime.jobs:live_chat_collect');
    processor.addEnvironment('JOB_HANDLER_REPLAY_CHAT_IMPORT', 'app.runtime.jobs:normalize');
    processor.addEnvironment('JOB_HANDLER_NORMALIZE', 'app.runtime.jobs:normalize');
    processor.addEnvironment('JOB_HANDLER_AGGREGATE', 'app.runtime.jobs:aggregate');
    processor.addEnvironment('JOB_HANDLER_WORDCLOUD', 'app.runtime.jobs:wordcloud');

    new events.Rule(this, 'MetadataSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.hours(6)),
      targets: [
        new targets.LambdaFunction(collector, {
          event: events.RuleTargetInput.fromObject({
            jobType: 'metadata_sync', targetId: officialChannelId.valueAsString, inputVersion: 'scheduled:full',
            scheduleBucketMinutes: 360,
            inputManifest: { maxUploadPages: 1, collectComments: true },
          }),
        }),
      ],
    });
    new events.Rule(this, 'MonthlyFullRefreshSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.days(30)),
      targets: [
        new targets.LambdaFunction(collector, {
          event: events.RuleTargetInput.fromObject({
            jobType: 'metadata_sync',
            targetId: officialChannelId.valueAsString,
            inputVersion: 'scheduled:monthly-full',
            scheduleBucketMinutes: 1440,
            inputManifest: { collectComments: true },
          }),
        }),
      ],
    });
    new events.Rule(this, 'LiveStartSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
      targets: [
        new targets.LambdaFunction(collector, {
          event: events.RuleTargetInput.fromObject({
            jobType: 'metadata_sync', targetId: officialChannelId.valueAsString, inputVersion: 'scheduled:live',
            scheduleBucketMinutes: 5,
            inputManifest: { maxUploadPages: 1, discoverLive: true },
          }),
        }),
      ],
    });
    new events.Rule(this, 'ExportSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.hours(24)),
      targets: [
        new targets.LambdaFunction(exporter, {
          event: events.RuleTargetInput.fromObject({
            targetId: 'public-release', inputVersion: 'scheduled:export', scheduleBucketMinutes: 1440,
            inputManifest: { candidatePrefix: 'candidates/latest' },
          }),
        }),
      ],
    });
    new events.Rule(this, 'OperationsHeartbeatSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.hours(1)),
      targets: [
        new targets.LambdaFunction(exporter, {
          event: events.RuleTargetInput.fromObject({ operation: 'operations_heartbeat' }),
        }),
      ],
    });

    const alarmAction = new cloudwatchActions.SnsAction(alerts);
    const dlqAlarm = deadLetterQueue.metricApproximateNumberOfMessagesVisible({
      period: cdk.Duration.minutes(5),
      statistic: 'Maximum',
    }).createAlarm(this, 'DlqAlarm', {
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    dlqAlarm.addAlarmAction(alarmAction);
    const workerErrors = new cloudwatch.MathExpression({
      expression: 'collector + processor + exporter',
      usingMetrics: {
        collector: collector.metricErrors(),
        processor: processor.metricErrors(),
        exporter: exporter.metricErrors(),
      },
      period: cdk.Duration.minutes(5),
    });
    const errorAlarm = workerErrors.createAlarm(this, 'WorkerErrorAlarm', {
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorAlarm.addAlarmAction(alarmAction);
    const quotaMetric = new cloudwatch.Metric({
      namespace: 'Diopside',
      metricName: 'YouTubeQuotaUnits',
      statistic: 'Sum',
      period: cdk.Duration.days(1),
    });
    const quotaAlarm = quotaMetric.createAlarm(this, 'Quota80Alarm', {
      threshold: 8000,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    quotaAlarm.addAlarmAction(alarmAction);
    const exportAgeMetric = new cloudwatch.Metric({
      namespace: 'Diopside',
      metricName: 'LatestExportAgeHours',
      statistic: 'Maximum',
      period: cdk.Duration.hours(1),
    });
    const exportAgeAlarm = exportAgeMetric.createAlarm(this, 'ExportFreshnessAlarm', {
      threshold: 24,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.BREACHING,
    });
    exportAgeAlarm.addAlarmAction(alarmAction);
    new budgets.CfnBudget(this, 'MonthlyCostBudget', {
      budget: {
        budgetType: 'COST',
        timeUnit: 'MONTHLY',
        budgetLimit: { amount: monthlyBudgetUsd.valueAsNumber, unit: 'USD' },
      },
      notificationsWithSubscribers: [{
        notification: {
          comparisonOperator: 'GREATER_THAN',
          notificationType: 'FORECASTED',
          threshold: 80,
          thresholdType: 'PERCENTAGE',
        },
        subscribers: [{ subscriptionType: 'SNS', address: alerts.topicArn }],
      }],
    });
    new cloudwatch.Dashboard(this, 'OperationsDashboard', {
      dashboardName: `${this.stackName}-operations`,
      widgets: [
        [new cloudwatch.GraphWidget({
          title: 'Worker errors',
          left: [collector.metricErrors(), processor.metricErrors(), exporter.metricErrors()],
        })],
        [new cloudwatch.GraphWidget({
          title: 'Queue depth and DLQ',
          left: [
            jobQueue.metricApproximateNumberOfMessagesVisible(),
            exportQueue.metricApproximateNumberOfMessagesVisible(),
            deadLetterQueue.metricApproximateNumberOfMessagesVisible(),
          ],
        })],
        [new cloudwatch.GraphWidget({ title: 'YouTube daily quota units', left: [quotaMetric] })],
        [new cloudwatch.GraphWidget({
          title: 'Export freshness and CDN synthetic success',
          left: [
            exportAgeMetric,
            new cloudwatch.Metric({
              namespace: 'Diopside', metricName: 'CdnSyntheticSuccess', statistic: 'Average',
            }),
          ],
        })],
      ],
    });

    const responseHeaders = new cloudfront.ResponseHeadersPolicy(this, 'SecurityHeaders', {
      securityHeadersBehavior: {
        contentSecurityPolicy: {
          contentSecurityPolicy: "default-src 'self'; img-src 'self' https://i.ytimg.com; frame-ancestors 'none'",
          override: true,
        },
        contentTypeOptions: { override: true },
        frameOptions: { frameOption: cloudfront.HeadersFrameOption.DENY, override: true },
        referrerPolicy: {
          referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
          override: true,
        },
        strictTransportSecurity: {
          accessControlMaxAge: cdk.Duration.days(365),
          includeSubdomains: true,
          override: true,
        },
      },
    });
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(publicData),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        responseHeadersPolicy: responseHeaders,
      },
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      enableLogging: true,
      logBucket: accessLogs,
      logFilePrefix: 'cloudfront/',
    });
    exporter.addEnvironment('DISTRIBUTION_ID', distribution.distributionId);
    exporter.addEnvironment('DISTRIBUTION_DOMAIN_NAME', distribution.domainName);
    exporterRole.addToPolicy(new iam.PolicyStatement({
      actions: ['cloudfront:CreateInvalidation'],
      resources: [
        `arn:${this.partition}:cloudfront::${this.account}:distribution/${distribution.distributionId}`,
      ],
    }));
    NagSuppressions.addResourceSuppressions(distribution, [
      {
        id: 'AwsSolutions-CFR4',
        reason: 'TLS_V1_2_2021 is configured; the finding is caused by the default CloudFront certificate.',
      },
      {
        id: 'AwsSolutions-CFR1',
        reason: 'The public archive has no geographic access-control requirement.',
      },
      {
        id: 'AwsSolutions-CFR2',
        reason: 'The distribution serves immutable static JSON/SVG only; WAF fixed cost exceeds the budget.',
      },
    ]);

    new cdk.CfnOutput(this, 'DistributionDomainName', { value: distribution.domainName });
    new cdk.CfnOutput(this, 'PublicBucketName', { value: publicData.bucketName });
    new cdk.CfnOutput(this, 'ControlTableName', { value: control.tableName });
    new cdk.CfnOutput(this, 'JobQueueUrl', { value: jobQueue.queueUrl });
    new cdk.CfnOutput(this, 'ExportQueueUrl', { value: exportQueue.queueUrl });
    new cdk.CfnOutput(this, 'DeadLetterQueueArn', { value: deadLetterQueue.queueArn });
    new cdk.CfnOutput(this, 'ConfigurationBucketName', { value: configuration.bucketName });
    new cdk.CfnOutput(this, 'OperationsAlertTopicArn', { value: alerts.topicArn });
  }

  private privateBucket(id: string, expirationDays: number, logs: s3.Bucket): s3.Bucket {
    return new s3.Bucket(this, id, {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(expirationDays),
          noncurrentVersionExpiration: cdk.Duration.days(expirationDays),
        },
      ],
      serverAccessLogsBucket: logs,
      serverAccessLogsPrefix: `s3/${id.toLowerCase()}/`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
  }

  private runtimeRole(id: string): iam.Role {
    const role = new iam.Role(this, id, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: [`arn:${this.partition}:logs:${this.region}:${this.account}:*`],
      }),
    );
    NagSuppressions.addResourceSuppressions(
      role,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'CDK bucket grants require object-key wildcards but remain scoped to named stack buckets.',
        },
      ],
      true,
    );
    return role;
  }

  private worker(id: string, role: iam.Role, queueUrl: string): lambda.Function {
    const handler = id === 'Collector'
      ? 'app.runtime.handlers.collector_handler'
      : id === 'Processor'
        ? 'app.runtime.handlers.processor_handler'
        : 'app.runtime.handlers.exporter_handler';
    return new lambda.Function(this, id, {
      runtime: lambda.Runtime.PYTHON_3_14,
      handler,
      code: lambda.Code.fromAsset(backendDirectory, {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: ['bash', '-c', 'pip install -r requirements-lambda.txt -t /asset-output && cp -R src/app /asset-output/app'],
          local: {
            tryBundle(outputDirectory: string): boolean {
              try {
                mkdirSync(outputDirectory, { recursive: true });
                execFileSync('uv', ['pip', 'install', '--target', outputDirectory, '-r', 'requirements-lambda.txt'], {
                  cwd: backendDirectory,
                  env: { ...process.env, UV_CACHE_DIR: '/tmp/diopside-uv-cache' },
                  stdio: 'ignore',
                });
                cpSync(path.join(backendDirectory, 'src/app'), path.join(outputDirectory, 'app'), {
                  recursive: true,
                });
                return true;
              } catch {
                return false;
              }
            },
          },
        },
      }),
      role,
      timeout: cdk.Duration.minutes(15),
      memorySize: 512,
      reservedConcurrentExecutions: 2,
      environment: { JOB_QUEUE_URL: queueUrl },
      tracing: lambda.Tracing.ACTIVE,
    });
  }
}
