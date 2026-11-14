// Assert that closed/superseded heads never download or publish an artifact.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const prepare = require('./preview-publish.cjs');
(async () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-test-'));
  process.env.RUNNER_TEMP = temp;
  const {previewBase} = require('./preview_config.cjs');
  const repo = {owner: 'owner', repo: 'repo'};
  const pages = {html_url: 'https://owner.github.io/repo/', cname: null, build_type: 'workflow'};
  assert.equal(previewBase(repo, pages), 'https://owner.github.io/repo/previews');
  for (const invalid of [
    {...pages, html_url: 'https://production.invalid/previews/'},
    {...pages, cname: 'production.invalid'},
    {...pages, html_url: 'http://owner.github.io/repo/'},
    {...pages, html_url: 'https://owner.github.io/other/'},
    {...pages, html_url: 'https://owner.github.io.evil.invalid/repo/'},
    {...pages, html_url: 'https://other.github.io/repo/'},
    {...pages, build_type: 'legacy'},
  ]) assert.throws(() => previewBase(repo, invalid), /default HTTPS GitHub Pages origin/);
  const pr = {number: 42, head: {sha: 'current', ref: 'feature', repo: {full_name: 'owner/repo'}}};
  const run = {id: 1, head_sha: 'old', head_branch: 'feature', head_repository: {full_name: 'owner/repo'}};
  let downloads = 0;
  let output;
  const github = {
    rest: {repos: {getPages: async () => ({data: pages})}, pulls: {list: 'pulls', listFiles: 'files'}, actions: {
      listWorkflowRunArtifacts: 'artifacts',
      downloadArtifact: async () => { downloads++; return {data: Buffer.from('zip')}; },
    }},
    paginate: async endpoint => ({pulls: [pr], files: [
      {filename: 'content/sensors/real-user-monitoring.md', status: 'added'},
      {filename: 'content/sensors/removed.md', status: 'removed'},
    ], artifacts: [{id: 2, name: 'pr-preview', expired: false, size_in_bytes: 3}]}[endpoint]),
  };
  const args = {github, context: {repo: {owner: 'owner', repo: 'repo'}, payload: {workflow_run: run}},
    core: {info() {}, setOutput: (key, value) => { output = value; }}};
  try {
    await prepare(args);
    assert.equal(downloads, 0);
    assert.equal(output, undefined);
    run.head_sha = 'current';
    await prepare(args);
    assert.equal(downloads, 1);
    assert.equal(output, 42);
    const data = JSON.parse(fs.readFileSync(path.join(temp, 'preview-links.json')));
    assert.equal(data.sha, 'current');
    assert(data.links.some(link => link.url.endsWith('/pr-42/sensors/real-user-monitoring/')));
    assert(!data.links.some(link => link.url.includes('removed')));
    console.log('Preview publisher: origin isolation, current-head, and changed-page checks passed.');
  } finally { fs.rmSync(temp, {recursive: true, force: true}); }
})().catch(error => { console.error(error); process.exit(1); });
