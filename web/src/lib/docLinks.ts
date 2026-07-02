const URL_PATTERN = /https?:\/\/[^\s)\]}>"']+/g;

const INTERNAL_LEARN_PATH_PARTS = [
  '/includes/',
  '/toc',
  '/model-matrix/',
  '/media/'
];

// GitHub source repos that mirror the public Learn articles. Used as a
// *last-resort* fallback: if a card still contains a `/includes/` Learn URL
// (i.e. the backend `include_link_resolver` was disabled or the resolution
// failed), we still want the user to be able to click through to the raw
// markdown source rather than a dead 404 link.
const LOCALE_PATTERN = /^[a-z]{2}-[a-z]{2}$/i;
const SOURCE_REPOS = {
  azureAiDocs: 'https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles',
  azureDocs: 'https://github.com/MicrosoftDocs/azure-docs/blob/main/articles'
};

export function extractUrls(markdown: string = '') {
  return Array.from(markdown.matchAll(URL_PATTERN))
    .map(match => match[0].replace(/[.,;:]+$/, ''))
    .filter((url, index, urls) => urls.indexOf(url) === index);
}

export function isLikelyInternalLearnUrl(url: string = '') {
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

export function isPublicLearnUrl(url: string = '') {
  try {
    const parsed = new URL(url);
    return parsed.hostname === 'learn.microsoft.com' && !isLikelyInternalLearnUrl(url);
  } catch {
    return false;
  }
}

/**
 * Build a GitHub-source URL for an internal-only Learn URL, so that
 * unresolved include fragments remain clickable (pointing to the raw
 * markdown file). Returns '' for URLs we cannot safely map.
 *
 * This is a client-side helper of last resort. Prefer server-side
 * resolution to the true parent Learn URL (see `include_link_resolver.py`).
 */
function toSourcePath(parts: string[]) {
  const sourcePath = parts.join('/');
  if (!sourcePath) return '';
  if (/\.[a-z0-9]+$/i.test(sourcePath)) return sourcePath;
  return parts[parts.length - 1] === 'toc' ? `${sourcePath}.yml` : `${sourcePath}.md`;
}

export function getLearnSourceUrl(url: string = '') {
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

/**
 * Return an openable URL for an arbitrary link.
 *
 * - If the URL is a normal public Learn URL (or any non-Learn URL), it is
 *   returned unchanged.
 * - If the URL is a Learn "internal" fragment (`/includes/`, `/toc`, etc.)
 *   that would 404 on learn.microsoft.com, and we can derive a GitHub
 *   source URL for it, that GitHub URL is returned instead.
 * - Otherwise the original URL is returned (better than nothing).
 */
export function getOpenableDocUrl(url: string = '') {
  if (!isLikelyInternalLearnUrl(url)) {
    return url;
  }
  return getLearnSourceUrl(url) || url;
}

export function getPrimaryDocUrl(markdown: string = '') {
  return extractUrls(markdown).find(isPublicLearnUrl) || '';
}
