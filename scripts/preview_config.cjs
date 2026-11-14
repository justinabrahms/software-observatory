// A different project path is not a different browser origin.
function previewRepository(value) {
  if (!/^[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9_][A-Za-z0-9_.-]*$/.test(value || '')) {
    throw new Error('Set PREVIEW_REPOSITORY to the dedicated owner/repository');
  }
  const [owner, repo] = value.split('/');
  return {owner, repo};
}

function previewBase(source, target, metadata) {
  if (target.owner.toLowerCase() === source.owner.toLowerCase() ||
      metadata.owner?.login.toLowerCase() !== target.owner.toLowerCase() ||
      metadata.name !== target.repo || metadata.has_pages !== true ||
      metadata.default_branch !== 'main') {
    throw new Error('Previews require a different account and an enabled Pages repository on main');
  }
  // Construct the only permitted host. Never accept a configurable base URL.
  return `https://${target.owner.toLowerCase()}.github.io/${target.repo}/previews`;
}

async function assertDefaultOrigin(base, request = fetch) {
  const home = base.slice(0, -'previews'.length);
  const response = await request(home, {redirect: 'manual'});
  if (response.status !== 200 || response.url !== home) {
    throw new Error('Default Pages origin unavailable or redirecting; custom domains are forbidden');
  }
}

async function assertNoSiblingPages(github, target) {
  const repos = await github.paginate(github.rest.repos.listForUser, {
    username: target.owner, per_page: 100,
  });
  for (const repo of repos) {
    if (repo.name.toLowerCase() === target.repo.toLowerCase()) continue;
    if (typeof repo.has_pages !== 'boolean') {
      throw new Error('Unable to verify the preview account Pages inventory');
    }
    if (repo.has_pages) {
      throw new Error('The preview account has another Pages site; its origin must be reserved for untrusted previews');
    }
  }
}
module.exports = {previewRepository, previewBase, assertNoSiblingPages, assertDefaultOrigin};
