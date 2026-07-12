import { readFileSync } from 'node:fs';

const latestPath = 'backend/data/public/latest.json';
const latest = JSON.parse(readFileSync(latestPath, 'utf8'));

console.log(JSON.stringify({
  service: 'diopside-infra',
  generatedAt: new Date().toISOString(),
  releaseId: latest.releaseId,
  releaseMode: latest.releaseMode,
  releaseContractPath: latest.indexPath,
  status: 'initial-plan-only',
  notes: [
    'CDK/runner layer is intentionally minimal for target bootstrap.',
    'Next steps: add VPC, OIDC policy guardrails, artifact bucket lifecycle, and report export pipeline.',
  ],
}, null, 2));
