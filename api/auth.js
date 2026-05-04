// Vercel Serverless Function — Decap CMS GitHub OAuth proxy
// Uses the request host dynamically so it works with custom domains.

export default async function handler(req, res) {
  const { GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET } = process.env;
  const { code } = req.query;

  // Determine the site URL from the request itself
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

    // Return HTML with postMessage to Decap CMS opener
    const token = data.access_token;
    const scope = data.scope || 'repo';
    res.setHeader('Content-Type', 'text/html');
    return res.send(`<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><title>Authorizing...</title></head>
<body>
<p>Authorization successful, redirecting...</p>
<script>
  (function() {
    var msg = 'authorization:${siteUrl}:${token}:${scope}';
    try {
      window.opener.postMessage(msg, '*');
    } catch(e) {
      // fallback: try location.origin
      try { window.opener.postMessage(msg, location.origin); } catch(e2) {}
    }
    setTimeout(function() { window.close(); }, 500);
  })();
</script>
</body>
</html>`);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
