# Part II: Building a Machine on a Static Page

# Chapter 5: Running a Machine on a Static Page — The COOP/COEP Wall, and One Ingenious Way Around It

> **"Are GitHub Pages sites static? Can you run a server on them?"**
> This is where the investigation turned. The answer: the site itself is not static at all, but no, you genuinely cannot run a traditional server on it. **And Wasm makes a third answer possible — you can move the server into the user's browser.**

## Scenario 1: First, separate three things — GitHub the site, GitHub Pages, and "running a server"

**Background.** These three get conflated constantly, producing a very common misconception: "GitHub is static."

**GitHub the site: not static at all.** When you browse a repository, open an issue or submit a pull request, you are looking at a highly dynamic page: heavy JavaScript on the front end (React components) handling live interaction, and GitHub's own large server fleet behind it (built mainly on Ruby on Rails) handling requests, databases and the filesystem.

**GitHub Pages: hosts static files only.** It serves the HTML, CSS, JS, images and `.wasm` in your repo through a CDN, unchanged.

- ❌ **Cannot**: run a Node.js / Django / Go backend process, listen on a port, connect to a database, run scheduled jobs.
- ⭕ **Can**: host a single-page app (React / Vue / Svelte), and **arbitrarily complex frontend computation driven by WebAssembly**.

**The other two places GitHub lets you "run things"** (worth clarifying, because people reach for them as substitutes):

| Service | What it can run | Hard limits |
|---|---|---|
| **GitHub Pages** | Static files plus everything browser-side (including Wasm) | No custom HTTP headers, no backend, no database |
| **GitHub Actions** | Any process inside a VM (Linux/Windows/macOS), including databases and servers | **Built for testing and packaging**: a single run has a time limit (commonly 6 hours per job on public repositories) and the VM is destroyed afterward — **it cannot be a permanent web host** |
| **GitHub Codespaces** | A complete cloud development container; you can `npm start` or `python manage.py runserver`, with automatic port forwarding to a temporary URL | For development; idles and sleeps — **not a production host** |

**The key connection**: if you want something that behaves like a backend inside a "static hosting environment," **Wasm is one of the answers.** Projects already exist (StackBlitz's **WebContainers**, for instance) that use Wasm to compile and run a substantial portion of the Node.js runtime and OS kernel inside the browser — the user opens a page, and the browser uses Wasm to "simulate" a backend server on the front end, needing no cloud host at all.

**And if you want to see this taken all the way**: **FluffOS** — a still-maintained LPMud driver (a modern fork of MudOS, written in C++) — has made **WebAssembly one of its official build targets**. The official README's words are "**the whole driver runs in a browser page — compiler, VM, efuns, telnet.**" Its mudlib (the source of an entire game world) is packed into a static bundle by Emscripten's `file_packager`, **requiring no server**. Which means a multiplayer game server with a heartbeat, timers, persistent world state, and a compiler for user code at runtime becomes three static files you can drop onto a CDN. **Full teardown in Appendix L.**

> ⚠️ Authenticity Caveat
> "WebContainers runs Node.js in the browser" is real and verifiable (StackBlitz's public engineering posts explain it in detail). But understand its boundary precisely: **it is not Node.js's C++ source compiled unchanged into Wasm**; it is a reimplemented runtime that executes on Wasm and is API-compatible with Node.js, using a Service Worker to intercept network requests and simulate server behaviour. **The precise version of "running a real server in the browser" is: simulating, inside the browser, a server whose behaviour is consistent for this page.** Other people on the open internet **cannot** reach that "server" by URL — not without P2P traversal on top.

> 💡 A Word to the Wise
> **"Static" and "dynamic" were never properties of a web page; they are properties of *which end the computation happens on*.** The same HTML file is static when it sits on a CDN, but the Wasm module it pulls up can finish a video transcode, run a SQL query, push a round of neural-network inference on the client. The computation did not decrease — **it merely changed who pays for it**, from your server bill to the user's CPU cycles and battery. The commercial implication far outweighs the technical one: **when an expensive cost can be transferred to users painlessly, and users feel no pain, that cost will be transferred.** Ad SDKs do it, cryptocurrency mining scripts do it, and Wasm lets legitimate heavy computation do it too. So the next time you see the words "zero server cost," get in the habit of appending the second half: **the cost did not disappear; it became someone else's electricity bill.**

## Scenario 2: The wall 90% of people hit — COOP / COEP

**Background.** Your FFmpeg.wasm runs beautifully under `python -m http.server` locally, and the moment you push it to GitHub Pages:

```
ReferenceError: SharedArrayBuffer is not defined
```

or

```
Uncaught DOMException: Failed to construct 'Worker': ... blocked by cross-origin isolation
```

**The full causal chain** (the key to everything; the fuse laid in Chapter 3 detonates here):

```
Spectre (2018, CPU speculative-execution side channel)
   ↓ the attack needs a high-resolution timer to measure cache timing
SharedArrayBuffer + Atomics can construct a nanosecond timer
   ↓ so browsers disabled SharedArrayBuffer by default across the board
   ↓ later restored, with a condition: the page must be "cross-origin isolated"
Cross-origin isolation requires the server to return two HTTP headers
   ↓
Cross-Origin-Opener-Policy: same-origin      ← severs window references from other origins
Cross-Origin-Embedder-Policy: require-corp   ← every cross-origin subresource must opt in
   ↓ when both hold, self.crossOriginIsolated === true
   ↓ only then does SharedArrayBuffer exist
   ↓ and Wasm multithreading depends on SharedArrayBuffer
   ↓
❌ GitHub Pages does not allow custom HTTP headers
   ↓
every multithreaded Wasm project (multithreaded FFmpeg.wasm,
parallel OpenCV, Emscripten pthread, Rust rayon-wasm…)
simply cannot run on GitHub Pages
```

**What each header defends against:**

- `Cross-Origin-Opener-Policy: same-origin` (COOP): severs the `window.opener` reference chain across origins, preventing windows from other origins from sharing an OS process with you (same process means same address space, which is Spectre's opening to read your memory).
- `Cross-Origin-Embedder-Policy: require-corp` (COEP): requires **every** cross-origin resource the page loads (images, scripts, iframes, fonts) to explicitly consent to being embedded — via a `Cross-Origin-Resource-Policy: cross-origin` response header, or through CORS. **Anything that hasn't opted in is blocked.**

**COEP's collateral damage is the painful part.** The moment you turn on cross-origin isolation, **every third-party resource without CORP/CORS headers breaks** — Google Fonts, CDN images, YouTube embeds, ads, analytics scripts. That is why, even if you *can* set headers (self-hosted Nginx, or Cloudflare Pages' `_headers`), enabling isolation is still a decision with a price.

> 💡 **The solution: `coi-serviceworker`**
> The open-source community produced an ingenious way around this. You include a script called **`coi-serviceworker`**, which uses the browser's **Service Worker** to intercept, **on the front end**, all requests the page itself makes, and "adds" the two headers to the responses.
> How: drop `coi-serviceworker.js` in the root of your GitHub Pages site and include it at the very top of `index.html`'s `<head>`:
> ```html
> <script src="coi-serviceworker.js"></script>
> ```
> On first load the Service Worker has not taken control yet, so the script reloads the page once; on the second load every response carries COOP/COEP, `crossOriginIsolated` becomes `true`, and `SharedArrayBuffer` appears.

**Why it is legitimate, and why it is safe.** A Service Worker is a proxy layer **registered by the same-origin page itself**, able to intercept only requests within its own scope. It does not bypass the browser's security model — **it declares, within the page's own authority, "I voluntarily enter the isolated state."** The browser accepts that declaration, because the cost of isolation (losing cross-origin resources) is borne by that same page.

**Its four costs** (know them, or you will be caught in production):

1. **One extra page load** (the Service Worker only takes effect after registration), so the first experience flickers.
2. **Requires HTTPS** (GitHub Pages has it by default; `localhost` also counts as a secure context).
3. **Cross-origin resources without CORP are still blocked** — identical to genuinely setting the headers; a Service Worker can only modify responses it can see.
4. **Service Workers have their own caching and update semantics**, so deploying a new version can leave users on the old one; you need to handle `skipWaiting` / `clients.claim`.

**When you don't need any of this.** **If your Wasm is single-threaded, you do not need COOP/COEP at all.** Most projects (`wasm-pack`'s default output, most parsers and compilers) are single-threaded and just work when pushed to GitHub Pages. **Confirm you genuinely need multithreading before paying this price.**

### Two options that cost less

**Option one: `COEP: credentialless` instead of `require-corp`.**

`require-corp` demands that every cross-origin subresource **actively opt in** to being embedded (by returning `Cross-Origin-Resource-Policy`) — and you have no control over whether third parties do. `credentialless` takes a different approach: **allow cross-origin resources that haven't opted in, but request them without credentials** (no cookies, no client certificates).

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless    ← far gentler than require-corp
```

**It still makes `crossOriginIsolated` true**, without killing off every public image and font that simply never set CORP. The cost: **cross-origin resources that require cookies become unreachable** (the request carries no credentials), and browser support is less uniform than `require-corp`. **Try `credentialless` first; fall back to `require-corp`.**

**Option two: switch to a backend that doesn't need `SharedArrayBuffer`.**

This one is routinely undervalued. Take persistent SQLite: the official SQLite-Wasm ships **two** OPFS VFS implementations. The first-generation `opfs` needs `SharedArrayBuffer` (and therefore isolation), while **`opfs-sahpool` needs no COOP/COEP at all and is the fastest option in the official documentation** (details in Chapter 7).

> 💡 **Plenty of teams have wrestled with `SharedArrayBuffer` and isolation for two weeks when the thing they wanted had a path that never needed it. Spend ten minutes reading whether your library has a second backend before you start.**

### And one more wall you may not have hit yet, but will: CSP

**If your site sets a Content-Security-Policy, Wasm compilation is blocked outright.**

The reason: `WebAssembly.compile()` / `instantiate()` / `compileStreaming()` count as **dynamic code generation** in CSP's eyes, in the same category as `eval()`. Early on the only workaround was enabling `'unsafe-eval'` — **which is handing over your entire XSS defence.**

**The current answer is a dedicated keyword:**

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'` **permits WebAssembly compilation only, and does not permit `eval()` or `new Function()`.** Support: **Chrome 97+, Firefox 102+, Safari 16+** (Chrome extensions can use it in the manifest's `content_security_policy` from v103).

**This bites in three situations in particular**: **(a)** your Wasm is embedded in someone else's iframe whose CSP doesn't allow it; **(b)** browser extensions; **(c)** corporate portals with a uniform CSP policy. **The symptom is a CSP violation error, not a Wasm error — which is why it so easily sends you looking in the wrong place.**

> 🔍 Deeper Commentary — `coi-serviceworker` is a "legitimate protocol loophole," and such things deserve wariness about their lifespan
> This workaround stands on a subtle premise in the security model: **the browser treats "the page voluntarily entering isolation" and "the server requiring the page to enter isolation" as equivalent in security terms**, because the thing isolation protects is that page itself. The reasoning is sound, so `coi-serviceworker` is not an exploit; it is a **correct use of the specification.** But two things deserve long-term wariness. **First, it depends on a combined behaviour that was never explicitly promised.** No line of specification says "COOP/COEP headers synthesized by a Service Worker must be treated as equivalent to those emitted by the server" — it is a natural inference each implementation drew. Any technique that relies on inferred behaviour at the intersection of several specifications carries the risk of being tightened in a future version. **Second, and more fundamentally: it reveals a structural fact — free static hosting gives you a CDN, gives you HTTPS, gives you version control, and gives you everything except control over response headers; and the Web's advanced capabilities (cross-origin isolation, CSP, Permissions Policy, Trusted Types, even some origin trials) are all fastened to response headers.** So the real lesson is not "learn to use coi-serviceworker" but — **when you choose a free platform, what you give up is often not what you need today, but the control you will need in two years.** A free platform's ceiling is always discovered at the moment you grow to a certain size, by which point the migration cost is already high. This resurfaces in another form in Chapters 11 and 12 on moats: **control is the only genuinely scarce thing.**

## Scenario 3: The complete deployment path, from `cargo` to that `github.io` URL

**Background.** Collapsing the theory into a path you can follow. Using the mainstream **Rust + WebAssembly** as the example.

**Step 1: build locally**

Use `wasm-pack` to compile Rust into web-targeted Wasm and JS glue:

```bash
wasm-pack build --target web
```

This produces a `pkg/` directory containing the `.wasm` and the `.js` glue.

**Choose `--target` correctly** (the most commonly misconfigured thing for newcomers):

| target | Output shape | For |
|---|---|---|
| `web` | An ES module, usable directly via `<script type="module">` | **The correct answer for static GitHub Pages deployment** |
| `bundler` | A module for webpack/rollup/vite (with `import` syntax) | Projects with a bundler |
| `nodejs` | CommonJS, for Node.js | Server side |
| `no-modules` | A traditional script hanging off a global | Old environments, or `importScripts` inside a Worker |

**Step 2: write the front-end HTML**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <!-- Only needed if you use multithreading, and it must come first -->
  <script src="coi-serviceworker.js"></script>
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <script type="module">
    import init, { greet } from './pkg/your_project.js';
    async function run() {
      await init();              // initialize the Wasm module (uses instantiateStreaming internally)
      greet("GitHub Pages");     // call a function inside Wasm
    }
    run();
  </script>
</body>
</html>
```

**Step 3: push and enable Pages**

1. Push the project (with `index.html` and `pkg/`) to a GitHub repository.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, publish from your branch (`main` or `gh-pages`).
4. Wait a few minutes and visit `https://<account>.github.io/<project>/`.

**Four traps you will definitely hit** (ordered by how often they catch people):

1. **`.gitignore` excluded `pkg/`.** Many Rust templates ignore the `pkg/` directory `wasm-pack` produces, so what you pushed is a site with no `.wasm`. **Fix**: either add `pkg/` to version control, or build in CI with GitHub Actions (below).
2. **Paths are relative, and project pages live under a subpath.** The subpath in `https://user.github.io/repo/` makes absolute paths like `/pkg/xxx.js` 404. **Fix**: use relative paths, `./pkg/xxx.js`.
3. **Jekyll ate the underscore-prefixed folder.** GitHub Pages runs Jekyll by default, which ignores files and folders beginning with `_`. **Fix**: put an empty `.nojekyll` file at the root.
4. **You forgot `await init()`.** Wasm loading is asynchronous; calling any exported function before initialization completes will blow up.

**Building and deploying automatically with GitHub Actions** (much cleaner than committing `pkg/` by hand):

```yaml
name: Deploy Wasm to Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown
      - name: Install wasm-pack
        run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - name: Build
        run: wasm-pack build --target web --release
      - name: Optimize
        run: |
          npm install -g binaryen
          wasm-opt -Oz --strip-debug pkg/*_bg.wasm -o pkg/tmp.wasm
          mv pkg/tmp.wasm pkg/$(ls pkg | grep _bg.wasm)
      - name: Assemble site
        run: |
          mkdir -p dist && cp index.html dist/
          cp -r pkg dist/ && touch dist/.nojekyll
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - uses: actions/deploy-pages@v4
```

> 💡 A Word to the Wise
> **The difficulty of a deployment path lies not in how many steps it has, but in how far the error message sits from the actual cause.** Each of those four traps has a lying error message: `pkg/` not pushed gives you a 404; absolute paths give you a 404; Jekyll eating your folder gives you — **still a 404**. Three completely different causes, one symptom. That is why "I followed the tutorial and it doesn't work" is the most common beginner frustration — **tutorials describe the happy path, while in reality you spend 90% of your time interpreting an error message pointing the wrong way.** Which means the genuinely valuable document is not a step list but a **symptom-to-cause table.** The same holds when you write your own tools, libraries and error messages: **a good error message is worth ten pages of tutorial.**

## Scenario 4: The four classic shapes of "what are people running up there"

**Background.** Before diving into a hundred and one cases, look at the four most typical shapes — the ones that best explain *why* anyone would do this.

**Shape one: shift the server's work onto the user — in-browser video editing (FFmpeg.wasm)**

Compile the C-language FFmpeg toolkit into Wasm. The user drags a video into a page on GitHub Pages, and **the transcode happens on the user's own CPU**, consuming none of your bandwidth.

- **The value is not speed; it's not paying.** A cloud transcoding service (something like AWS MediaConvert) bills by the minute and eats enormous upload bandwidth; FFmpeg.wasm's marginal cost is zero.
- **A privacy dividend comes along for free.** The user's video never leaves their computer. For personal video, medical imaging or internal corporate material, that argument is more persuasive than performance.

**Shape two: bring the dead back — retro game emulators in the browser**

Many Game Boy, NES and PS1 emulators written in C++ or Rust are compiled to Wasm, hosted on GitHub Pages, playable the moment you open the page.

- **Why Wasm is decisive**: an emulator needs to simulate CPU cycles **clock-accurately.** JavaScript's timers are imprecise and garbage collection pauses at random, producing audio/video desync and pops. Wasm's performance curve is flat — exactly what an emulator wants.

**Shape three: push AI to the edge — in-browser inference (ONNX Runtime Web)**

Load a lightweight model (object detection, face recognition) on GitHub Pages and run it through Wasm in real time, **saving even the cost of server AI silicon.**

- **Wasm's role here is the fallback.** WebGPU/WebGL backends are faster but depend on drivers and hardware; the Wasm CPU backend runs on anything. **This is a choice about availability, not performance.**

**Shape four: move the entire server in — a MUD driver in the browser (FluffOS × Wasm)**

The first three shapes move a **function** across — feed it input, take its output. **The fourth is different: it moves a server that has a heartbeat, state, and stays alive.**

- **Why it is harder than the first three**: a MUD driver is not a request handler. It has heartbeats, `call_out` timers, persistent world state, multiple concurrent connections — **and it compiles the mudlib's LPC source into bytecode at runtime**, so the compiler and virtual machine have to come into the browser too.
- **How it solves "the browser cannot block"**: the native driver blocks inside libevent's event loop, which is a dead end in a browser. The solution is **handing ownership of the loop to the host** — the page calls the exported `fluffos_tick(now_ms)` on a `setInterval`, which advances the scheduler, drains due events and returns immediately. **The scheduling core is shared with the native build; only who rings the bell differs**, so the mudlib needs no changes at all.
- **The costs**: no sockets (DNS is stubbed to return `127.0.0.1`), no threads, no TLS (the browser owns that), and **writes currently survive only within the page session** (MEMFS; an IDBFS/OPFS overlay is still on the roadmap).

**This shape pushes "static hosting plus Wasm" to its logical conclusion**: an entire persistent multiplayer world becomes three static files. **See Appendix L.**

**What the four shapes have in common** (the skeleton of Part II):

```
    what the server used to do
          ↓
    ┌─────────────────┐
    │ heavy, expensive │  ← the algorithm itself is public (FFmpeg, emulators,
    │ dense computation│     ONNX inference) — no trade secret, only compute cost
    │ with no secrets  │
    └─────────────────┘
          ↓ compiled to Wasm
    ┌─────────────────┐
    │ executed in the  │  ← cost goes to zero, privacy improves, concurrency unlimited
    │ user's browser   │     price: first-load size, device heat, battery
    └─────────────────┘
```

**And conversely, what cannot be pushed out**: anything touching keys, authentication, billing, and any core algorithm whose leak would end the company. **That line is what all four chapters of Part III are about drawing.**

## Chapter Summary

- **GitHub the site is not static; GitHub Pages is.** Pages hosts files only; Actions is a CI environment with a time limit that is destroyed afterward; Codespaces is a development container that sleeps. **None of the three is a permanent host — and Wasm offers a fourth road: move the server into the browser.**
- **COOP/COEP is the number one obstacle to running Wasm on static hosting**, and the full causal chain is: Spectre → `SharedArrayBuffer` disabled → restored but requiring cross-origin isolation → isolation requiring two HTTP headers → **GitHub Pages won't let you set headers** → multithreaded Wasm dies.
- **`coi-serviceworker`** synthesizes those two headers on the front end via a Service Worker — a correct use of the specification, not an exploit. Costs: one extra load, HTTPS required, **cross-origin resources without CORP are still blocked**, and Service Worker update semantics.
- **Two cheaper options**: **`COEP: credentialless`** (allows resources that never opted in, requested without credentials — far gentler than `require-corp`), and **switching to a backend that doesn't need `SharedArrayBuffer`** (SQLite-Wasm's `opfs-sahpool` VFS, which **needs no isolation and is the fastest**, Chapter 7).
- **Confirm you genuinely need multithreading** — most Wasm projects are single-threaded and just work when pushed, without touching any of this.
- **CSP is another wall you will eventually hit**: Wasm compilation counts as dynamic code generation, and **the answer is `script-src 'wasm-unsafe-eval'`** (Chrome 97+ / Firefox 102+ / Safari 16+), which permits Wasm compilation without permitting `eval()`. **The symptom is a CSP violation, not a Wasm error, which sends people looking in the wrong place.**
- The four deployment traps (`pkg/` gitignored, absolute paths 404, Jekyll eating underscore folders, forgetting `await init()`) **all produce a 404 with completely different causes** — the root of "I followed the tutorial and it doesn't work."
- The four classic shapes share one structure: **push "heavy, expensive, algorithmically public" computation into the user's browser.** The fourth shape (FluffOS moving an entire MUD driver into a tab, with `fluffos_tick` handing loop ownership to the host) takes that to its conclusion — **an entire persistent multiplayer world = three static files** (Appendix L). What cannot be pushed out is Part III's subject.
- **The second half of "zero server cost" is always: the cost did not disappear; it became someone else's electricity bill.**

The wall is crossed and the machine is running. So — **what exactly are people running up there?** That list of a hundred and twenty starts getting taken apart in the next chapter. Turn to Chapter 6.
