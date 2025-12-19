# Dynamic Product List from Config

**Date**: December 19, 2025  
**Type**: Feature Enhancement  
**Impact**: Web UI

## Summary

Modified the web UI to dynamically load product list from `target_config.json` instead of using hard-coded product names. This allows the product dropdown to automatically reflect changes in the configuration file without requiring code modifications.

## Changes Made

### 1. New API Endpoint: `/api/products`

**File**: `web/src/app/api/products/route.ts` (New)

- Reads `target_config.json` from the project root directory
- Extracts unique `topic_name` values while preserving order
- Implements robust error handling with fallback to hard-coded list
- Returns JSON response with product list and metadata

**Key Features**:
- Automatic deduplication of topic names (handles multiple language configs)
- Comprehensive error logging to console
- Graceful fallback to predefined product list on any error
- Returns source information (config or fallback) for debugging

### 2. Frontend Updates: `page.tsx`

**File**: `web/src/app/page.tsx`

**Changes**:
- Added `getProducts()` function to fetch product list from API
- Replaced hard-coded product array with dynamic state (`products`)
- Added `currentProduct` state to properly track selected product
- Implemented automatic default product selection from config file
- Added URL parameter synchronization

**New State Management**:
```typescript
const [products, setProducts] = useState<string[]>(FALLBACK_PRODUCTS);
const [currentProduct, setCurrentProduct] = useState<string>(...);
```

**New Effects**:
- Fetch products on component mount
- Auto-select first product from config if URL has no product parameter
- Sync `currentProduct` state when URL parameters change

### 3. Fallback Mechanism

**File**: Both `route.ts` and `page.tsx`

Hard-coded fallback product list maintained in both files:
```typescript
const FALLBACK_PRODUCTS = [
  'AI-Foundry',
  'AOAI-V2',
  'Agent-Service',
  'Model-Inference',
  'AML',
  'Cog-speech-service',
  'Cog-document-intelligence',
  'Cog-language-service',
  'Cog-translator',
  'Cog-content-safety',
  'Cog-computer-vision',
  'Cog-custom-vision-service',
  'IoT-iot-hub',
  'IoT-iot-edge',
  'IoT-iot-dps',
  'IoT-iot-central',
  'IoT-iot-hub-device-update'
];
```

## Error Handling

Three-layer error handling strategy:

1. **API Layer** (`route.ts`):
   - File not found → fallback + log error
   - JSON parse error → fallback + log error
   - No topics found → fallback + log error

2. **Fetch Layer** (`getProducts()`):
   - Network error → fallback + log error
   - API returns fallback → log warning

3. **Component Layer**:
   - Initial state uses fallback
   - Ensures UI always has data to display

## Benefits

1. **Maintainability**: Product list changes only require updating `target_config.json`
2. **Consistency**: Product dropdown always matches actual configuration
3. **Reliability**: Multiple fallback mechanisms prevent UI breakage
4. **Debugging**: Comprehensive error logging for troubleshooting

## Testing Notes

- Tested with config containing single product (`AI-Foundry-test`)
- Verified URL parameter synchronization
- Confirmed fallback behavior when config is missing
- Validated product selection and data fetching flow

## Migration Guide

No migration required. Existing deployments will continue to work:
- If `target_config.json` is not found, uses fallback list
- Backward compatible with existing URL parameters
- No breaking changes to existing functionality

## Future Considerations

- Could extend to also read languages from config
- Consider caching product list to reduce file reads
- Potential to add config file hot-reloading
