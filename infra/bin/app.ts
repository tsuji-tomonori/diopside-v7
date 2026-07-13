#!/usr/bin/env node
import 'source-map-support/register.js';

import * as cdk from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';

import { DiopsideStack } from '../lib/diopside-stack.js';

const app = new cdk.App();
new DiopsideStack(app, 'DiopsideStack', {
  description: '低costかつevent駆動のdiopside収集・静的公開stack',
});
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
