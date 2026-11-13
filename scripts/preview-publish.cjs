// Runs from the default branch in the privileged publisher. Never execute PR code.
module.exports = async ({github, context, core}) => {
  const fs = require('fs');
  const run = context.payload.workflow_run;
  const pulls = await github.paginate(github.rest.pulls.list, {...context.repo, state: 'open'});
  const pr = pulls.find(p => p.head.sha === run.head_sha &&
    p.head.repo?.full_name === run.head_repository.full_name && p.head.ref === run.head_branch);
  if (!pr) { core.info('PR closed or head superseded; skipping'); return; }
  const base = process.env.PREVIEW_BASE_URL;
  if (!base || !base.startsWith('https://')) throw new Error('Set PREVIEW_BASE_URL');
  const url = `${base.replace(/\/$/, '')}/pr-${pr.number}`;
  const links = [
    {label: 'Home', url: `${url}/`},
    {label: 'Runtime catalog', url: `${url}/catalog/#runtime`},
    {label: 'Atlas', url: `${url}/atlas/`},
  ];
  const files = await github.paginate(github.rest.pulls.listFiles, {...context.repo, pull_number: pr.number});
  for (const file of files) {
    const match = /^content\/sensors\/([a-z0-9-]+)\.md$/.exec(file.filename);
    if (match && file.status !== 'removed') links.push({label: match[1], url: `${url}/sensors/${match[1]}/`});
  }
  const artifacts = await github.paginate(github.rest.actions.listWorkflowRunArtifacts,
    {...context.repo, run_id: run.id});
  const artifact = artifacts.find(a => a.name === 'pr-preview' && !a.expired);
  if (!artifact) throw new Error('Missing preview artifact');
  if (artifact.size_in_bytes > 100_000_000) throw new Error('Preview archive too large');
  const zip = await github.rest.actions.downloadArtifact({...context.repo, artifact_id: artifact.id, archive_format: 'zip'});
  fs.writeFileSync(`${process.env.RUNNER_TEMP}/preview.zip`, Buffer.from(zip.data));
  fs.writeFileSync(`${process.env.RUNNER_TEMP}/preview-links.json`, JSON.stringify({sha: pr.head.sha, links}));
  core.setOutput('number', pr.number);
};
