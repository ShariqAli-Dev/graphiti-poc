# Rate Limiting Guide

## Problem

When uploading files to Graphiti, you may see rate limit errors from OpenAI:

```
HTTP/1.1 429 Too Many Requests
Rate limit exceeded. Please try again later.
```

This happens when too many concurrent API calls are made during entity extraction.

## Solution: Adjust SEMAPHORE_LIMIT

The `SEMAPHORE_LIMIT` environment variable controls how many concurrent OpenAI API calls Graphiti makes during entity extraction.

**CRITICAL:** Graphiti reads `SEMAPHORE_LIMIT` at import time, not runtime. You MUST call `load_dotenv()` BEFORE importing `graphiti_core`, otherwise it will use the default value (20) instead of your configured value.

### Current Setting

Check your `.env` file:

```bash
SEMAPHORE_LIMIT=3
```

### Recommended Values

**IMPORTANT:** Even on paid tiers, keep SEMAPHORE_LIMIT low to avoid burst rate limits!

| OpenAI Tier | SEMAPHORE_LIMIT | UPLOAD_DELAY_SECONDS | Upload Speed | Rate Limit Risk |
|-------------|-----------------|----------------------|--------------|-----------------|
| **Free** | 3 | 2-3 | Slow | Very Low |
| **Tier 1** | 5 | 1-2 | Medium | Low |
| **Tier 2** | 8 | 1 | Fast | Low |
| **Tier 3+** | 10 | 0.5-1 | Very Fast | Medium |

**Why lower is better even on paid tier:**
- OpenAI has burst rate limits (requests per second)
- 20 concurrent requests = 20 requests hitting API within ~100ms
- This triggers burst protection even if your RPM limit is high
- Lower concurrency + delay = more reliable, predictable uploads

### How to Adjust

1. **Open `.env` file:**
   ```bash
   nano .env
   ```

2. **Adjust both settings:**
   ```env
   # SEMAPHORE_LIMIT: Controls concurrency within each file upload
   # Lower = less concurrent API calls = safer
   SEMAPHORE_LIMIT=8

   # UPLOAD_DELAY_SECONDS: Delay between file uploads in batch mode
   # Prevents sustained bursts when uploading multiple files
   UPLOAD_DELAY_SECONDS=1
   ```

3. **Restart the CLI:**
   ```bash
   python3 cli.py
   ```

### Understanding UPLOAD_DELAY_SECONDS

**What it does:**
- Adds a pause between file uploads when using "Upload Directory" (Option 2)
- Does NOT affect single file uploads (Option 1)
- Spreads API load over time instead of hammering OpenAI continuously

**When to use:**
- ✅ **Always use 1+ seconds for batch uploads** (safer)
- ✅ Batch uploading 5+ files
- ✅ When you've hit rate limits before
- ❌ Don't need for single file uploads

**Example:**
```env
# Without delay (risky for batches):
UPLOAD_DELAY_SECONDS=0

# With delay (safer):
UPLOAD_DELAY_SECONDS=1
```

Result:
```
Without delay:
File 1 (8 concurrent) → File 2 (8 concurrent) → File 3 (8 concurrent)
└─ Sustained 8 concurrent calls → May hit TPM limits

With 1s delay:
File 1 (8 concurrent) → [wait 1s] → File 2 (8 concurrent) → [wait 1s] → File 3
└─ Gives OpenAI time to "reset" → Much safer
```

### Understanding the Tradeoff

- **Lower value (2-3):**
  - ✅ Avoids rate limits
  - ✅ Safer for free/low tier
  - ❌ Slower file uploads
  - ❌ More time to process documents

- **Higher value (10-20):**
  - ✅ Faster file uploads
  - ✅ Better for batch operations
  - ❌ May hit rate limits
  - ❌ Requires paid tier

### Finding Your Tier

Check your OpenAI rate limits:
1. Go to https://platform.openai.com/account/limits
2. See your "Requests per minute (RPM)" limit
3. Set SEMAPHORE_LIMIT to roughly 10-20% of your RPM limit

Example:
- RPM limit: 500 → SEMAPHORE_LIMIT = 10
- RPM limit: 3500 → SEMAPHORE_LIMIT = 20
- RPM limit: 10000 → SEMAPHORE_LIMIT = 50

### Testing Your Settings

1. **Start with low value (3):**
   ```env
   SEMAPHORE_LIMIT=3
   ```

2. **Upload a test file:**
   ```bash
   python3 cli.py
   # Select: 1 (Upload File)
   ```

3. **Monitor for rate limit errors in logs**

4. **If no errors, gradually increase:**
   ```env
   SEMAPHORE_LIMIT=5  # Try this
   ```

5. **Repeat until you find the sweet spot**

### What Happens During Upload

Graphiti performs these operations for each document:

1. **Extract entities** (LLM calls)
2. **Deduplicate entities** (LLM calls)
3. **Extract relationships** (LLM calls)
4. **Create embeddings** (LLM calls)

With `SEMAPHORE_LIMIT=3`, Graphiti will:
- Make 3 concurrent API calls at a time
- Wait for one to finish before starting another
- Process the entire document gradually

With `SEMAPHORE_LIMIT=20`, Graphiti will:
- Make 20 concurrent API calls
- Process much faster
- **BUT** hit rate limits on free/low tiers

### Batch Upload Recommendations

When uploading many files (Option 2: Upload Directory):

**Free Tier:**
```env
SEMAPHORE_LIMIT=2
```

**Paid Tier:**
```env
SEMAPHORE_LIMIT=10
```

Then upload overnight or during off-hours.

### Emergency: Already Hit Rate Limit

If you're currently rate limited:

1. **Stop the upload** (Ctrl+C)

2. **Lower the limit:**
   ```env
   SEMAPHORE_LIMIT=2
   ```

3. **Wait 60 seconds** (OpenAI rate limit window)

4. **Try again**

### Advanced: Per-Model Limits

Different OpenAI models have different rate limits:

| Model | Typical RPM (Tier 1) |
|-------|---------------------|
| gpt-4o-mini | 500 |
| gpt-4o | 500 |
| gpt-4 | 500 |
| gpt-3.5-turbo | 3500 |

Set SEMAPHORE_LIMIT accordingly.

### Monitoring

Watch the logs during upload:

```bash
# Good (no rate limits):
2025-10-17 23:37:15 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 200 OK"

# Bad (rate limited):
2025-10-17 23:37:22 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 429 Too Many Requests"
```

If you see 429 errors, lower SEMAPHORE_LIMIT.

## Summary

1. **Start conservative:** `SEMAPHORE_LIMIT=3`
2. **Monitor for 429 errors**
3. **Increase gradually** if no errors
4. **Find your sweet spot**
5. **When in doubt, go lower** (slower but safer)

---

**Pro tip:** For large batch uploads, set a low SEMAPHORE_LIMIT and run overnight. It's better to be slow and successful than fast and rate-limited.
