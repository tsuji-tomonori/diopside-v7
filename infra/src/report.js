import { readFileSync, writeFileSync } from 'node:fs';

const manifest = JSON.parse(readFileSync('../backend/data/public/latest.json', 'utf8'));
const snapshot = {
  scope: 'ops',
  releaseId: manifest.releaseId,
  mode: manifest.releaseMode,
  checkItems: [
    'public contract available',
    'ui route contract consumed',
    'policy consent key present',
    'save/history/local storage versioned',
  ],
  generatedAt: new Date().toISOString(),
};

writeFileSync('infra/.cache-operation-report.json', JSON.stringify(snapshot, null, 2));
console.log('report saved: infra/.cache-operation-report.json');
