const URL_PATTERN = /https?:\/\/[^\s)\]}>"']+/g;

const INTERNAL_LEARN_PATH_PARTS = [
  '/includes/',
  '/toc',
  '/model-matrix/',
  '/media/'
];

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

export function getPrimaryDocUrl(markdown: string = '') {
  return extractUrls(markdown).find(isPublicLearnUrl) || '';
}
