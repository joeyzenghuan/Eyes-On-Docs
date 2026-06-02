const URL_PATTERN = /https?:\/\/[^\s)\]}>"']+/g;

const INTERNAL_LEARN_PATH_PARTS = [
  '/includes/',
  '/toc',
  '/model-matrix/',
  '/media/'
];

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

function toSourcePath(parts: string[]) {
  const sourcePath = parts.join('/');
  if (!sourcePath) {
    return '';
  }

  if (/\.[a-z0-9]+$/i.test(sourcePath)) {
    return sourcePath;
  }

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

export function getOpenableDocUrl(url: string = '') {
  if (!isLikelyInternalLearnUrl(url)) {
    return url;
  }

  return getLearnSourceUrl(url) || url;
}

export function getPrimaryDocUrl(markdown: string = '') {
  return extractUrls(markdown).find(isPublicLearnUrl) || '';
}
