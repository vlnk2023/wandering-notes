const DEFAULT_REPO = "vlnk2023/wandering-notes";

function sendJson(res, status, payload) {
  res.status(status).json(payload);
}

function getAuthToken(req) {
  const header = req.headers.authorization || "";
  const bearer = header.match(/^Bearer\s+(.+)$/i);
  return bearer ? bearer[1] : req.headers["x-editor-token"];
}

function assertEditorAuth(req) {
  const expected = process.env.EDITOR_TOKEN;
  if (!expected) {
    const error = new Error("EDITOR_TOKEN is not configured");
    error.status = 500;
    throw error;
  }

  if (getAuthToken(req) !== expected) {
    const error = new Error("Invalid editor token");
    error.status = 401;
    throw error;
  }
}

function assertGithubConfig() {
  if (!process.env.GITHUB_TOKEN) {
    const error = new Error("GITHUB_TOKEN is not configured");
    error.status = 500;
    throw error;
  }
}

function normalizePostPath(value) {
  const normalized = String(value || "").replace(/\\/g, "/");
  const isPost = normalized.startsWith("data/posts/") && normalized.endsWith(".md");
  const isSafe = !normalized.includes("..") && !normalized.startsWith("/");

  if (!isPost || !isSafe) {
    const error = new Error("Invalid post path");
    error.status = 400;
    throw error;
  }

  return normalized;
}

function githubPath(path) {
  return path.split("/").map(encodeURIComponent).join("/");
}

async function parseBody(req) {
  if (Buffer.isBuffer(req.body)) return JSON.parse(req.body.toString("utf8") || "{}");
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") return JSON.parse(req.body || "{}");

  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString("utf8");
  return raw ? JSON.parse(raw) : {};
}

async function githubFetch(path, options = {}) {
  const repo = process.env.GITHUB_REPO || DEFAULT_REPO;
  const url = `https://api.github.com/repos/${repo}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      "X-GitHub-Api-Version": "2022-11-28",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const error = new Error(data.message || `GitHub API failed with ${response.status}`);
    error.status = response.status;
    error.details = data;
    throw error;
  }

  return data;
}

async function getFile(path) {
  const branch = process.env.GITHUB_BRANCH || "main";
  const data = await githubFetch(`/contents/${githubPath(path)}?ref=${encodeURIComponent(branch)}`);
  const content = Buffer.from(String(data.content || "").replace(/\n/g, ""), "base64").toString("utf8");

  return {
    path,
    sha: data.sha,
    content,
    html_url: data.html_url,
  };
}

async function updateFile(path, content, sha, message) {
  const branch = process.env.GITHUB_BRANCH || "main";
  const body = {
    branch,
    message: message || `Update ${path}`,
    content: Buffer.from(content, "utf8").toString("base64"),
    sha,
  };

  return githubFetch(`/contents/${githubPath(path)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function triggerDeployHook() {
  const hook = process.env.VERCEL_DEPLOY_HOOK_URL;
  if (!hook) return null;

  try {
    const response = await fetch(hook, { method: "POST" });
    return { ok: response.ok, status: response.status };
  } catch (error) {
    return { ok: false, error: error.message };
  }
}

export default async function handler(req, res) {
  try {
    if (!["GET", "PUT"].includes(req.method)) {
      res.setHeader("Allow", "GET, PUT");
      return sendJson(res, 405, { error: "Method not allowed" });
    }

    assertEditorAuth(req);
    assertGithubConfig();

    if (req.method === "GET") {
      const path = normalizePostPath(req.query.path);
      const file = await getFile(path);
      return sendJson(res, 200, file);
    }

    const body = await parseBody(req);
    const path = normalizePostPath(body.path);
    const content = String(body.content || "");

    if (!content.trim()) {
      return sendJson(res, 400, { error: "Content cannot be empty" });
    }

    const current = await getFile(path);
    if (body.sha && body.sha !== current.sha) {
      return sendJson(res, 409, {
        error: "This post changed after you loaded it. Reload before saving.",
        currentSha: current.sha,
      });
    }

    const update = await updateFile(path, content, current.sha, body.message);
    const deployHook = await triggerDeployHook();

    return sendJson(res, 200, {
      ok: true,
      path,
      commit: update.commit?.sha,
      html_url: update.content?.html_url,
      deployHook,
    });
  } catch (error) {
    return sendJson(res, error.status || 500, {
      error: error.message || "Unexpected error",
      details: error.details,
    });
  }
}
