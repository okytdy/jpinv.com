import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildHomepageReports } from './lib/compounder-home-news.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'content/compounders/profile-data.json'), 'utf8'));
buildHomepageReports(root, data);
