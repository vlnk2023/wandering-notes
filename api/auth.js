// Vercel Serverless Function — Decap CMS GitHub OAuth proxy
// https://decapcms.org/docs/external-oauth-clients/

export default async function handler(req, res) {
  const { GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, SITE_URL } = process.env;
  const { code, type } = req.query;

  // Step 1: redirect to GitHub OAuth login
  if (!code) {
    const redirectUri = `${SITE_URL || 'https://wandering-notes.vercel.app'}/api/auth`;
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

    // Decap CMS expects the token in a script that posts to the opener window
    res.setHeader('Content-Type', 'text/html');
    return res.status(200).send(`
      <html>
      <head><meta charset="utf-8"/></head>
      <body>
      <script>
        (function() {
          function receiveMessage(e) {
            window.opener.postMessage(
              'authorization:${SITE_URL || 'https://wandering-notes.vercel.app'}:${data.access_token}:${data.scope || 'repo'}',
              e.origin
            );
            window.close();
          }
          window.addEventListener('message', receiveMessage, false);
          window.opener.postMessage('authorizing:${SITE_URL || 'https://wandering-notes.vercel.app'}', '*');
        })();
      </script>
      </body>
      </html>
    `);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
