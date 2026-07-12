#!/usr/bin/env node
import 'source-map-support/register.js';

import * as cdk from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';

import { DiopsideStack } from '../lib/diopside-stack.js';

const app = new cdk.App();
new DiopsideStack(app, 'DiopsideStack', {
  description: 'Low-cost event-driven diopside collection and static publication stack',
});
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
