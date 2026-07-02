// Node.js runner for the docLinks TypeScript file — since we don't have
// ts-node set up in this repo, this test rewrites the essential logic in
// pure JS and verifies the same behavior our TS file must exhibit. If the
// TS file changes shape (function signatures, return values), this test
// will need to be updated in parallel.

// Mirrors the logic in web/src/lib/docLinks.ts. Keep in sync manually.
const LOCALE_PATTERN = /^[a-z]{2}-[a-z]{2}$/i;
const INTERNAL_LEARN_PATH_PARTS = ['/includes/', '/toc', '/model-matrix/', '/media/'];
const SOURCE_REPOS = {
  azureAiDocs: 'https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles',
  azureDocs: 'https://github.com/MicrosoftDocs/azure-docs/blob/main/articles'
};

function isLikelyInternalLearnUrl(url = '') {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== 'learn.microsoft.com') return false;
    const pathname = parsed.pathname.toLowerCase();
    return INTERNAL_LEARN_PATH_PARTS.some(part => pathname.includes(part));
  } catch {
    return false;
  }
}

function toSourcePath(parts) {
  const sourcePath = parts.join('/');
  if (!sourcePath) return '';
  if (/\.[a-z0-9]+$/i.test(sourcePath)) return sourcePath;
  return parts[parts.length - 1] === 'toc' ? `${sourcePath}.yml` : `${sourcePath}.md`;
}

function getLearnSourceUrl(url = '') {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== 'learn.microsoft.com') return '';
    const parts = parsed.pathname.split('/').filter(Boolean);
    if (parts.length > 0 && LOCALE_PATTERN.test(parts[0])) parts.shift();
    if (parts[0] !== 'azure') return '';
    const azurePath = parts.slice(1);
    const [productRoot, ...rest] = azurePath;
    if (!productRoot || rest.length === 0) return '';
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
  if (!isLikelyInternalLearnUrl(url)) return url;
  return getLearnSourceUrl(url) || url;
}

const cases = [
  // 1. Backend resolved (public Learn URL) — should pass through unchanged.
  {
    name: 'public Learn URL passes through unchanged',
    in: 'https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision',
    outEquals: 'https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision',
    isInternal: false,
  },
  // 2. Unresolved /includes/ — should map to GitHub source.
  {
    name: 'unresolved /includes/ maps to GitHub source',
    in: 'https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content',
    outEquals: 'https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/foundry/openai/includes/how-to-gpt-with-vision-content.md',
    isInternal: true,
  },
  // 3. Unresolved /includes/ under unknown product root — fallback fails,
  //    UpdateCard should show grey span.
  {
    name: 'unknown product root => no source URL',
    in: 'https://learn.microsoft.com/en-us/azure/some-mystery-service/includes/foo',
    outEquals: 'https://learn.microsoft.com/en-us/azure/some-mystery-service/includes/foo',  // openable === in => grey span
    isInternal: true,
  },
  // 4. Non-Learn URL (github, external) — pass through.
  {
    name: 'non-Learn URL passes through',
    in: 'https://github.com/MicrosoftDocs/azure-ai-docs/pull/123',
    outEquals: 'https://github.com/MicrosoftDocs/azure-ai-docs/pull/123',
    isInternal: false,
  },
];

let failed = 0;
for (const c of cases) {
  const isInternal = isLikelyInternalLearnUrl(c.in);
  const out = getOpenableDocUrl(c.in);
  const okInternal = isInternal === c.isInternal;
  const okOut = out === c.outEquals;
  if (okInternal && okOut) {
    console.log(`PASS  ${c.name}`);
  } else {
    failed += 1;
    console.log(`FAIL  ${c.name}`);
    console.log(`      in:    ${c.in}`);
    console.log(`      out:   ${out}`);
    console.log(`      want:  ${c.outEquals}`);
    console.log(`      internal got=${isInternal} want=${c.isInternal}`);
  }
}
console.log(failed ? `\n${failed} failure(s)` : `\nAll ${cases.length} tests passed.`);
process.exit(failed ? 1 : 0);
