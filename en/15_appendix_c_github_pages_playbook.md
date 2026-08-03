# Appendix C: The GitHub Pages × Wasm Deployment Playbook

> This one is a "follow it and it runs" operations manual. Chapter 5 explains why; this explains how.

---

## 1. Decide First: Do You Actually Need Threads?

**This is the most important fork in the whole playbook**, and taking the wrong branch costs two extra weeks.

```
Does your Wasm use pthread / rayon / SharedArrayBuffer?
│
├─ No (most projects)
│   → Deploy directly. No coi-serviceworker, no special configuration at all
│   → Skip to "2. The single-threaded deployment path"
│
└─ Yes → Ask three questions in order, and stop as early as you can:
    │
    ├─ ① Does the library you depend on have a backend that doesn't need SharedArrayBuffer?
    │     Example: SQLite-Wasm's opfs-sahpool VFS (no COOP/COEP, and fastest — Chapter 7)
    │     → Yes → ★ Use it. The entire problem disappears
    │
    ├─ ② Can your workload be partitioned? (batch processing, tiled rendering, independent queries)
    │     → Yes → ★ Switch to "multi-instance isolation" (N Workers × N Wasm instances)
    │              No cross-origin isolation needed, and it breaks the 4 GB ceiling too (Chapter 8)
    │
    └─ ③ Do you genuinely need fine-grained shared state (physics simulation, graph traversal)?
          → Yes → Go with coi-serviceworker, and try COEP: credentialless first
          → Skip to "3. The multithreaded deployment path"
```

---

## 2. The Single-Threaded Deployment Path

### Step 1: Compile

```bash
# Rust
wasm-pack build --target web --release

# C/C++
emcc app.cpp -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -o pkg/app.js
```

### Step 2: Optimize (strongly recommended — usually cuts 15–40% of the size)

```bash
wasm-opt -Oz --strip-debug --strip-producers \
  pkg/your_project_bg.wasm -o pkg/your_project_bg.wasm
```

### Step 3: `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <input type="file" id="file">
  <p id="status">Initializing…</p>

  <script type="module">
    // ★ Must use a relative path (./), or a project page's subpath will 404
    import init, { process } from './pkg/your_project.js';

    const status = document.getElementById('status');

    async function main() {
      await init();                        // ★ Always await, or calls blow up
      status.textContent = 'Wasm ready';

      document.getElementById('file').addEventListener('change', async (e) => {
        const buf = new Uint8Array(await e.target.files[0].arrayBuffer());
        const t0 = performance.now();
        const out = process(buf);          // one call handles the whole batch — keep the boundary coarse
        status.textContent = `Done in ${(performance.now() - t0).toFixed(1)} ms`;
      });
    }
    main();
  </script>
</body>
</html>
```

### Step 4: Project layout and `.nojekyll`

```
your-repo/
├── index.html
├── .nojekyll          ← ★ an empty file, stopping Jekyll from swallowing folders starting with _
└── pkg/
    ├── your_project.js
    └── your_project_bg.wasm
```

### Step 4.5: If your site has a CSP

In CSP's eyes, compiling Wasm is dynamic code generation, and **without an allowance it is simply blocked**:

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'` (Chrome 97+ / Firefox 102+ / Safari 16+) **permits Wasm compilation without permitting `eval()`**.
**The symptom is a CSP violation rather than a Wasm error** — which bites especially often in two situations: being embedded inside someone else's iframe, and browser extensions.

### Step 5: Turn on Pages

1. Push to GitHub.
2. **Settings → Pages → Build and deployment**.
3. Choose the source branch (`main` or `gh-pages`) and folder (`/` or `/docs`).
4. Wait a few minutes and visit `https://<account>.github.io/<project>/`.

---

## 3. The Multithreaded Deployment Path (needs `SharedArrayBuffer`)

### Step 1: Get `coi-serviceworker.js`

Fetch the script from its open-source repository and place it at the site root.

### Step 2: Include it at the very top of `<head>`

```html
<head>
  <script src="coi-serviceworker.js"></script>   <!-- ★ must be the first script -->
  <meta charset="UTF-8">
  ...
</head>
```

**Behaviour**: on the first load the Service Worker has not taken over yet, so the script reloads the page once automatically; from the second load onward every response carries COOP/COEP and `self.crossOriginIsolated === true`.

### Step 3: Verify

```javascript
console.log('crossOriginIsolated:', self.crossOriginIsolated);   // must be true
console.log('SharedArrayBuffer:', typeof SharedArrayBuffer);     // must be "function"
```

### Step 4: Enable threads at compile time

```bash
# Emscripten
emcc app.cpp -O3 -pthread -s PTHREAD_POOL_SIZE=4 \
     -s ALLOW_MEMORY_GROWTH=1 -o pkg/app.js

# Rust (rayon + wasm-bindgen-rayon)
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  rustup run nightly wasm-pack build --target web -- -Z build-std=panic_abort,std
```

### ⚠️ What breaks once isolation is on

> 💡 **Try `COEP: credentialless` before `require-corp`**: the former allows loading cross-origin resources that haven't opted in (it simply requests them without credentials), which sharply reduces the damage in the table below. Solutions of the `coi-serviceworker` kind can usually be configured to synthesize either one.

| What breaks | Why | Fix |
|---|---|---|
| Google Fonts / external CDN fonts | No `Cross-Origin-Resource-Policy` header | Self-host the fonts same-origin |
| Third-party images | Same as above | Self-host, or confirm the other side supports CORS and add the `crossorigin` attribute |
| YouTube / external iframes | Blocked by COEP | Switch to `credentialless` mode (limited support) or remove them |
| Ad / analytics scripts | Same as above | Usually there is nothing to do but remove them |

**This is exactly why Chapter 5 says "confirm you really need threads first" — the cost is real.**

---

## 4. Automated Build and Deploy with GitHub Actions

**Far cleaner than committing `pkg/` by hand**: source and artifacts stay separate, and every push is a reproducible build.

```yaml
name: Build & Deploy Wasm to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown

      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Install wasm-pack
        run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

      - name: Build
        run: wasm-pack build --target web --release

      - name: Install binaryen & optimize
        run: |
          npm install -g binaryen
          for f in pkg/*_bg.wasm; do
            wasm-opt -Oz --strip-debug --strip-producers "$f" -o "$f.opt"
            mv "$f.opt" "$f"
          done
          ls -lh pkg/*.wasm

      - name: Assemble site
        run: |
          mkdir -p dist
          cp index.html dist/
          cp -r pkg dist/
          # copy coi-serviceworker.js too if you need threads
          [ -f coi-serviceworker.js ] && cp coi-serviceworker.js dist/ || true
          touch dist/.nojekyll

      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## 5. Troubleshooting Table (ordered by how often people hit it)

| Symptom | Cause | Fix |
|---|---|---|
| `.wasm` 404 | `pkg/` was ignored by `.gitignore` | Commit it, or build with Actions instead |
| `.wasm` 404 | An absolute path `/pkg/...` was used, but the site lives under the `/repo/` subpath | Change everything to relative paths `./pkg/...` |
| `.wasm` 404 | Jekyll ignored a folder starting with `_` | Put an empty `.nojekyll` at the root |
| `Incorrect response MIME type` | The server didn't return `application/wasm` | GitHub Pages serves the `.wasm` extension correctly; if it fails, check the filename really ends in `.wasm` |
| `SharedArrayBuffer is not defined` | No cross-origin isolation | Bring in `coi-serviceworker` (see §3) |
| `undefined is not a function` when calling | You forgot `await init()` | Put every call after `await init()` |
| First load works; after deploying a new build you get the old one | Service Worker cache | Handle `skipWaiting()` / `clients.claim()` in the SW, or add a version query string to resources |
| Works locally, crashes in production | Locally you were on `localhost` (treated as a secure origin); production isn't | Verify HTTPS and the isolation state |
| Crashes outright on phones | The memory ceiling is far lower than on desktop | Lower the initial memory, switch to streaming in chunks (Chapter 8) |
| First load is extremely slow | The module is too large | `wasm-opt -Oz` + Brotli + module splitting with lazy loading |

---

## 6. Pre-Launch Checklist

```
□ wasm-opt -Oz has been run, and the size is acceptable (front end: < 30 MB recommended, < 10 MB ideal)
□ Section budget reviewed with wasm-objdump -h (if Data dominates, cut data first, not flags)
□ twiggy top / dominators confirms there is no unexpected size culprit
□ The release build has strip = true / lto = true (Chapter 9)
□ strings app.wasm | grep -Ei 'sk-|AKIA|password|secret' comes back empty  ★ most important
□ Every path is relative
□ .nojekyll exists
□ await init() precedes every call
□ TypedArray views are re-acquired after memory.grow
□ Large files go through streaming chunks; nothing is read in all at once
□ Heavy computation runs in a Worker; the main thread is never blocked
□ If using threads: crossOriginIsolated is true, and third-party resources have been checked for COEP damage
□ You checked first whether a backend exists that needs no SharedArrayBuffer (e.g. SQLite's opfs-sahpool)
□ If the site has a CSP: script-src already includes 'wasm-unsafe-eval'
□ The server returns Content-Type: application/wasm and Content-Encoding: br (pre-compressed .wasm.br beats on-the-fly)
□ The .wasm uses a content-hashed filename (stable URL → return visits hit the code cache)
□ When measuring, the cross-origin isolation state was consistent (timers are coarsened when not isolated)
□ With several Workers, postMessage the WebAssembly.Module rather than recompiling in each
□ A symbol-bearing build artifact is kept for reconstructing stacks from production issues
□ It has been tested on the target devices (including low-end phones), not only on the dev machine
```
