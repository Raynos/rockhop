/** Original opaque boxer and canonical body rest controls, with no deformation claim. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { checkPair } from './geometry-check.mjs';
const [input, output] = process.argv.slice(2); assert(input && output && !fs.existsSync(output));
const bytes = fs.readFileSync(input), document = JSON.parse(bytes), records = {};
for (const region of ['body', 'head', 'boxer']) assert(document.parts[region], 'Every original rest control is required');
for (const [a, b] of [['body', 'body'], ['body', 'head'], ['head', 'head'], ['body', 'boxer'], ['boxer', 'boxer']]) records[`${a}/${b}`] = checkPair(document.parts[a], document.parts[b], a === b);
fs.writeFileSync(output, JSON.stringify({ status: 'UNACCEPTED_ORIGINAL_SOURCE_REST_CONTACT_DIAGNOSTIC', ...Object.fromEntries(Object.entries(document).filter(([key]) => key !== 'parts')), restDataSHA256: crypto.createHash('sha256').update(bytes).digest('hex'), records }, null, 2) + '\n');
