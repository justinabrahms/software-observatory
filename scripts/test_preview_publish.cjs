const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const prepare = require('./preview-publish.cjs');
const {previewRepository, previewBase, assertNoSiblingPages, assertDefaultOrigin} = require('./preview_config.cjs');
(async () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-test-'));
  process.env.RUNNER_TEMP = temp;
  process.env.PREVIEW_REPOSITORY = 'preview-owner/previews';
  const source = {owner: 'owner', repo: 'repo'};
  const target = previewRepository(process.env.PREVIEW_REPOSITORY);
  const metadata = {owner: {login: 'preview-owner'}, name: 'previews', has_pages: true, default_branch: 'main'};
  assert.equal(previewBase(source, target, metadata), 'https://preview-owner.github.io/previews/previews');
  // The original error: a different project on the same owner's origin.
  assert.throws(() => previewBase(source, {owner: 'OWNER', repo: 'other'},
    {...metadata, owner: {login: 'owner'}, name: 'other'}), /different account/);
  for (const invalid of [
    {...metadata, has_pages: false},
    {...metadata, owner: {login: 'other'}},
    {...metadata, name: 'other'},
    {...metadata, default_branch: 'other'},
  ]) assert.throws(() => previewBase(source, target, invalid), /different account/);
  await assert.rejects(() => assertDefaultOrigin('https://preview.invalid/project/previews',
    async () => ({status: 301, url: 'https://preview.invalid/project/'})), /custom domains/);
  await assert.rejects(() => assertDefaultOrigin('https://preview.invalid/project/previews',
    async () => ({status: 200, url: 'https://trusted.invalid/'})), /custom domains/);
  const originalFetch = global.fetch;
  global.fetch = async url => ({status: 200, url});
  for (const invalid of [undefined, 'owner', 'owner/repo/extra', '../repo']) {
    assert.throws(() => previewRepository(invalid), /PREVIEW_REPOSITORY/);
  }
  const pr = {number: 42, head: {sha: 'current', ref: 'feature', repo: {full_name: 'owner/repo'}}};
  const run = {id: 1, head_sha: 'old', head_branch: 'feature', head_repository: {full_name: 'owner/repo'}};
  let downloads = 0;
  let output;
  let siblingSite = false;
  let unreadable = false;
  const github = {
    rest: {repos: {listForUser: 'repos', get: async () => ({data: metadata})}, pulls: {list: 'pulls', listFiles: 'files'}, actions: {
      listWorkflowRunArtifacts: 'artifacts',
      downloadArtifact: async () => { downloads++; return {data: Buffer.from('zip')}; },
    }},
    paginate: async endpoint => ({repos: [{name: 'previews', has_pages: true}, {name: 'other-repo', has_pages: unreadable ? undefined : siblingSite}], pulls: [pr], files: [
      {filename: 'content/sensors/real-user-monitoring.md', status: 'added'},
      {filename: 'content/sensors/removed.md', status: 'removed'},
    ], artifacts: [{id: 2, name: 'pr-preview', expired: false, size_in_bytes: 3}]}[endpoint]),
  };
  const args = {github, context: {repo: source, payload: {workflow_run: run}},
    core: {info() {}, setOutput: (key, value) => { output = value; }}};
  try {
    await prepare(args);
    assert.equal(downloads, 0);
    assert.equal(output, undefined);
    run.head_sha = 'current';
    siblingSite = true;
    await assert.rejects(() => prepare(args), /another Pages site/);
    assert.equal(downloads, 0); // Reject before obtaining any untrusted content.
    siblingSite = false;
    unreadable = true;
    await assert.rejects(() => assertNoSiblingPages(github, target), /Unable to verify/);
    unreadable = false;
    await prepare(args);
    assert.equal(downloads, 1);
    assert.equal(output, 42);
    const data = JSON.parse(fs.readFileSync(path.join(temp, 'preview-links.json')));
    assert.equal(data.sha, 'current');
    assert(data.links.some(link => link.url.endsWith('/pr-42/sensors/real-user-monitoring/')));
    assert(!data.links.some(link => link.url.includes('removed')));
    console.log('Preview publisher: rejects same-owner origins, sibling Pages sites, unreadable configuration, and stale heads.');
  } finally { global.fetch = originalFetch; fs.rmSync(temp, {recursive: true, force: true}); }
})().catch(error => { console.error(error); process.exit(1); });
