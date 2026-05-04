// Vercel Serverless Function — Decap CMS GitHub OAuth proxy
// Uses the request host dynamically so it works with custom domains.

export default async function handler(req, res) {
  const { GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET } = process.env;
  const { code } = req.query;

  // Determine the site URL from the request itself (works with any custom domain)
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const siteUrl = `https://${host}`;

  // Step 1: redirect to GitHub OAuth login
  if (!code) {
    const redirectUri = `${siteUrl}/api/auth`;
    const params = new URLSearchParams({
      client_id: GITHUB_CLIENT_ID,
      redirect_uri: redirectUri,
      scope: 'repo user',
    });
    return res.redirect(`https://github.com/login/oauth/authorize?${params}`);
  }

  // Step 2: exchange code for access token
  try {
    const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        client_id: GITHUB_CLIENT_ID,
        client_secret: GITHUB_CLIENT_SECRET,
        code,
      }),
    });

    const data = await tokenRes.json();

    if (data.error) {
      return res.status(400).json({ error: data.error_description || data.error });
    }

    // Return HTML that sends the token to the Decap CMS opener window and closes
    res.setHeader('Content-Type', 'text/html');
    const responseHtml = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body>
<script>
  window.opener.postMessage(
    'authorization:${siteUrl}:${data.access_token}:${data.scope || 'repo'}',
    '${siteUrl}'
  );
  window.close();
</script>
</body>
</html>`;
    return res.status(200).send(responseHtml);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
