#!/usr/bin/env node

const DEFAULT_BASE_URL = process.env.DOCS_BASE_URL || 'https://docs.westiedoubao.com';
const URL_PATTERN = /https?:\/\/[^\s)\]}>"']+/g;
const INTERNAL_LEARN_PATH_PARTS = ['/includes/', '/toc', '/model-matrix/', '/media/'];
const LOCALE_PATTERN = /^[a-z]{2}-[a-z]{2}$/i;
const SOURCE_REPOS = {
  azureAiDocs: 'https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles',
  azureDocs: 'https://github.com/MicrosoftDocs/azure-docs/blob/main/articles'
};

function parseArgs(argv) {
  const args = {
    baseUrl: DEFAULT_BASE_URL,
    language: 'Chinese',
    updateType: 'single',
    pages: 1,
    products: [],
    failOnBroken: false
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    if (arg === '--base-url' && next) {
      args.baseUrl = next;
      i += 1;
    } else if (arg === '--product' && next) {
      args.products.push(next);
      i += 1;
    } else if (arg === '--products' && next) {
      args.products.push(...next.split(',').map(value => value.trim()).filter(Boolean));
      i += 1;
    } else if (arg === '--language' && next) {
      args.language = next;
      i += 1;
    } else if (arg === '--update-type' && next) {
      args.updateType = next;
      i += 1;
    } else if (arg === '--pages' && next) {
      args.pages = Number.parseInt(next, 10);
      i += 1;
    } else if (arg === '--fail-on-broken') {
      args.failOnBroken = true;
    }
  }

  if (!Number.isInteger(args.pages) || args.pages < 1) {
    throw new Error('--pages must be a positive integer');
  }

  return args;
}

function extractUrls(text = '') {
  return Array.from(text.matchAll(URL_PATTERN))
    .map(match => match[0].replace(/[.,;:]+$/, ''))
    .filter((url, index, urls) => urls.indexOf(url) === index);
}

function isLikelyInternalLearnUrl(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== 'learn.microsoft.com') {
      return false;
    }

    const pathname = parsed.pathname.toLowerCase();
    return INTERNAL_LEARN_PATH_PARTS.some(part => pathname.includes(part));
  } catch {
    return false;
  }
}

function toSourcePath(parts) {
  const sourcePath = parts.join('/');
  if (!sourcePath) {
    return '';
  }

  if (/\.[a-z0-9]+$/i.test(sourcePath)) {
    return sourcePath;
  }

  return parts[parts.length - 1] === 'toc' ? `${sourcePath}.yml` : `${sourcePath}.md`;
}

function getLearnSourceUrl(url = '') {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== 'learn.microsoft.com') {
      return '';
    }

    const parts = parsed.pathname.split('/').filter(Boolean);
    if (parts.length > 0 && LOCALE_PATTERN.test(parts[0])) {
      parts.shift();
    }

    if (parts[0] !== 'azure') {
      return '';
    }

    const azurePath = parts.slice(1);
    const [productRoot, ...rest] = azurePath;

    if (!productRoot || rest.length === 0) {
      return '';
    }

    if (productRoot === 'foundry' || productRoot === 'foundry-classic' || productRoot === 'ai-services') {
      return `${SOURCE_REPOS.azureAiDocs}/${toSourcePath([productRoot, ...rest])}`;
    }

    if (productRoot === 'machine-learning' || productRoot.startsWith('iot-')) {
      return `${SOURCE_REPOS.azureDocs}/${toSourcePath(azurePath)}`;
    }

    return '';
  } catch {
    return '';
  }
}

function getOpenableDocUrl(url = '') {
  if (!isLikelyInternalLearnUrl(url)) {
    return url;
  }

  return getLearnSourceUrl(url) || url;
}

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
      'User-Agent': 'eyes-on-docs-link-audit/1.0'
    }
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${url}`);
  }

  return response.json();
}

async function checkUrl(url) {
  for (const method of ['HEAD', 'GET']) {
    try {
      const response = await fetch(url, {
        method,
        redirect: 'follow',
        headers: {
          'User-Agent': 'eyes-on-docs-link-audit/1.0'
        }
      });

      if (response.ok) {
        return { status: response.status, ok: true };
      }

      if (method === 'GET') {
        return { status: response.status, ok: false };
      }
    } catch (error) {
      if (method === 'GET') {
        return { status: 'ERR', ok: false, error: error.message };
      }
    }
  }

  return { status: 'ERR', ok: false };
}

async function getProducts(baseUrl) {
  const data = await fetchJson(`${baseUrl}/api/products`);
  return data.products || [];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const products = args.products.length > 0 ? args.products : await getProducts(args.baseUrl);
  const findings = [];

  for (const product of products) {
    for (let page = 1; page <= args.pages; page += 1) {
      const params = new URLSearchParams({
        product,
        language: args.language,
        page: String(page),
        updateType: args.updateType
      });
      const data = await fetchJson(`${args.baseUrl}/api/updates?${params.toString()}`);
      const updates = data.updates || [];

      for (const update of updates) {
        const urls = extractUrls(update.gptSummary || '');
        if (update.commitUrl) {
          urls.push(update.commitUrl);
        }

        for (const url of urls) {
          const internal = isLikelyInternalLearnUrl(url);
          const targetUrl = getOpenableDocUrl(url);
          const result = await checkUrl(targetUrl);
          findings.push({
            product,
            page,
            updateId: update.id,
            title: update.title,
            url,
            targetUrl,
            internal,
            status: result.status,
            ok: result.ok,
            error: result.error
          });
        }
      }
    }
  }

  const broken = findings.filter(item => !item.ok);
  const summary = {
    baseUrl: args.baseUrl,
    products,
    pagesPerProduct: args.pages,
    totalLinks: findings.length,
    brokenLinks: broken.length,
    internalSourceLinks: findings.filter(item => item.internal).length,
    brokenInternalSourceLinks: broken.filter(item => item.internal).length
  };

  console.log(JSON.stringify({ summary, broken }, null, 2));

  if (args.failOnBroken && broken.length > 0) {
    process.exitCode = 1;
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
