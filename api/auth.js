// Vercel Serverless Function — Decap CMS GitHub OAuth proxy
// Decap CMS 3.x expects: authorization:github:success:{"token":"...","scope":"..."}
// with a handshake: authorizing:github

export default async function handler(req, res) {
  const { GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET } = process.env;
  const { code } = req.query;

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
      res.setHeader('Content-Type', 'text/html');
      return res.send(`<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body>
<script>
  window.opener.postMessage('authorization:github:error:${JSON.stringify({error: data.error_description || data.error})}', '${siteUrl}');
  setTimeout(function() { window.close(); }, 500);
</script>
</body></html>`);
    }

    // Phase 1: send handshake, wait for CMS to respond
    // Phase 2: send actual authorization token
    const authData = JSON.stringify({ token: data.access_token, scope: data.scope || 'repo' });
    res.setHeader('Content-Type', 'text/html');
    return res.send(`<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><title>Authorizing...</title></head>
<body>
<script>
  (function() {
    // Phase 1: handshake
    window.opener.postMessage('authorizing:github', '${siteUrl}');

    // Phase 2: send authorization token
    function sendToken() {
      window.opener.postMessage(
        'authorization:github:success:${authData}',
        '${siteUrl}'
      );
    }

    // Wait for handshake response from CMS, or just send after timeout
    function onMessage(e) {
      if (e.data === 'authorizing:github' && e.origin === '${siteUrl}') {
        sendToken();
        setTimeout(function() { window.close(); }, 1000);
      }
    }
    window.addEventListener('message', onMessage, false);

    // Fallback: if CMS doesn't respond within 3s, send token anyway
    setTimeout(function() {
      window.removeEventListener('message', onMessage);
      sendToken();
      setTimeout(function() { window.close(); }, 1000);
    }, 3000);
  })();
</script>
</body>
</html>`);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
