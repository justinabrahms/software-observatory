// Preview content is untrusted. Require the default Pages origin, never a CNAME.
function previewBase(repo, pages) {
  const url = new URL(pages.html_url);
  const expectedHost = `${repo.owner.toLowerCase()}.github.io`;
  if (pages.cname || pages.build_type !== 'workflow' ||
      url.protocol !== 'https:' || url.hostname !== expectedHost ||
      url.port || url.username || url.password || url.search || url.hash ||
      url.pathname !== `/${repo.repo}/`) {
    throw new Error('Previews require the default HTTPS GitHub Pages origin with no custom domain');
  }
  return `${url.origin}${url.pathname}previews`;
}
module.exports = {previewBase};
