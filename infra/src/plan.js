import { readFileSync } from 'node:fs';

const latest = JSON.parse(readFileSync('../backend/data/public/latest.json', 'utf8'));

console.log(JSON.stringify({
  service: 'diopside-infra',
  generatedAt: new Date().toISOString(),
  releaseId: latest.releaseId,
  releaseMode: latest.releaseMode,
  releaseContractPath: latest.indexPath,
  status: 'cdk-synth-ready',
  architecture: {
    compute: 'scheduled and SQS-triggered Lambda',
    storage: 'versioned encrypted S3 + DynamoDB on-demand',
    queue: 'encrypted SQS + DLQ',
    delivery: 'private S3 origin + CloudFront OAC',
    fixedCostNetwork: false,
  },
  verification: ['npm test -w @diopside/infra', 'npm run synth -w @diopside/infra'],
  deploymentPerformed: false,
}, null, 2));
