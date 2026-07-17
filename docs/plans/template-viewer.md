# Amail Template Preview — Micro Project

> A real-time visual preview tool for email templates during development. Vite + React + Tailwind frontend with email client simulation.

---

## 1. Objective

Provide developers with a live, interactive preview of email templates as they're being built, including simulation of how they render across different email clients (Gmail, Outlook, Apple Mail) and device sizes.

---

## 2. Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | Vite + React + TypeScript | Fast dev, type safety |
| Styling | Tailwind CSS v4 | Rapid UI iteration |
| Proxy server | Node.js Express | Lightweight, serves as rendering bridge |
| Rendering | Python subprocess / amail API | Jinja2 rendering in same env as production |
| File watching | Chokidar | Hot-reload when template files change |

---

## 3. Project Structure

```
amail-templates/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── index.html
│
├── proxy-server/
│   ├── index.js                  # Express server entry
│   ├── renderer.js               # Calls amail API (or subprocess Jinja2)
│   ├── watcher.js                # Chokidar watches amail/templates/
│   └── websocket.js              # WebSocket for hot-reload push
│
└── src/
    ├── main.tsx
    ├── App.tsx
    │
    ├── components/
    │   ├── Layout.tsx            # Sidebar + preview pane split
    │   ├── TemplateList.tsx      # Sidebar: template file list
    │   ├── VariableEditor.tsx    # Auto-generated form from metadata
    │   ├── VariableField.tsx     # Single field: text/toggle/json
    │   ├── PreviewPane.tsx       # iframe + toolbar
    │   ├── PreviewToolbar.tsx    # Client sim, device toggle, dark mode
    │   ├── ClientDropdown.tsx    # Gmail / Outlook / Apple / Generic
    │   ├── DeviceToggle.tsx      # Desktop / Mobile / Tablet
    │   ├── DarkModeToggle.tsx
    │   ├── RawHTML.tsx           # Collapsible source viewer
    │   └── LoadingSkeleton.tsx
    │
    ├── hooks/
    │   ├── useTemplates.ts       # GET templates list + metadata
    │   ├── usePreview.ts         # Debounced render request → iframe srcdoc
    │   ├── useClientSim.ts       # CSS overlay per client
    │   ├── useDeviceSize.ts      # iframe width toggling
    │   └── useWebSocket.ts       # Hot-reload on file changes
    │
    ├── lib/
    │   ├── api.ts                # Proxy server REST calls
    │   ├── clientSimulations.ts  # CSS override rules per email client
    │   ├── renderService.ts      # Build render request payload
    │   └── defaultVariables.ts   # Default values per template type
    │
    └── styles/
        ├── index.css             # Tailwind imports + custom
        └── simulations.css       # Email client simulation overrides
```

---

## 4. Rendering Architecture

### Two options for server-side Jinja2 rendering:

**Option A (Recommended): Add render endpoint to amail**

```
POST /api/v1/templates/render
{
  "template": "action",
  "data": { "message": "Hello", "cta_text": "Click", ... }
}

→ 200
{ "html": "<!DOCTYPE html>...", "metadata": { ... } }
```

- Pro: Same Jinja2 environment as production, no drift
- Pro: Reuses existing `services/templates.py`
- Con: Requires amail server running

**Option B: Node.js subprocess calls Python CLI**

```
proxy-server/renderer.js
  → spawn("python3", ["-c", "from app.services.templates import render_template; ..."])
```

- Pro: Standalone, no amail server needed
- Con: Python env setup, slower per-request, env drift

**Fallback during dev:** If amail is running, use Option A (proxy forwards). If not, Option B.

### Render request flow

```
User edits variable → debounce 300ms → POST /api/render → iframe updates srcdoc
                                                                    ↓
                                                        ClientSim CSS injected
                                                                    ↓
                                                        Device width applied
```

### Debouncing

- Variable changes: 300ms debounce before calling render
- Template file changes: immediate via Chokidar notification

---

## 5. Variable Editor

### Auto-generated from template metadata

The `GET /api/v1/templates` endpoint returns per-template metadata:

```json
{
  "name": "action",
  "description": "Call-to-action email",
  "variables": [
    { "name": "message", "type": "string", "required": true, "description": "Main body" },
    { "name": "cta_text", "type": "string", "required": false, "description": "Button label" },
    { "name": "cta_url", "type": "string", "required": false, "description": "Button URL" },
    { "name": "notification", "type": "object", "required": false, "description": "Extra notice" }
  ]
}
```

### Field types → Input components

| `type` | Component |
|--------|-----------|
| `string` | `<input type="text">` |
| `number` | `<input type="number">` |
| `boolean` | Toggle switch |
| `object` | JSON textarea (with syntax highlight) |

### Default values per variable

A `defaultVariables.ts` file provides sensible defaults:

```typescript
const defaults: Record<string, Record<string, any>> = {
  action: {
    message: "Welcome! Click the button below to get started.",
    cta_text: "Get Started",
    cta_url: "https://example.com/action",
    expiry: "30 minutes",
    brand_name: "MyApp",
  },
  notification: { message: "Your report is ready.", heading: "New Update" },
  verification: { code: "482931", expiry: "10 minutes" },
  custom: { content: "<p>Your custom content here</p>" },
};
```

### Presets (localStorage)

- "Save current as preset" → stores all variable values in localStorage
- "Load preset" → dropdown of saved presets
- "Reset to defaults" → clears to defaults

---

## 6. Email Client Simulation

### How it works

Each simulation injects a CSS overlay + modifies the iframe `srcdoc` before rendering. The iframe is sandboxed with `sandbox="allow-scripts"` to prevent external requests while allowing JS-based CSS injection.

### Client simulation CSS overrides

```typescript
// lib/clientSimulations.ts
export const simulations: Record<string, Simulation> = {
  generic: {
    name: "Generic",
    css: "",
    bodyFilter: "",
  },
  gmail: {
    name: "Gmail",
    css: `
      /* Gmail strips <style> in head, relies on inline styles */
      .gmail-override { width: 100% !important; }
      table { width: 100% !important; }
    `,
    bodyFilter: "Strip <style> tags from head, enforce inline-only",
  },
  outlook: {
    name: "Outlook",
    css: `
      /* Outlook uses Word rendering engine */
      body { max-width: 600px !important; }
      * { mso-line-height-rule: exactly; }
    `,
  },
  apple_mail: {
    name: "Apple Mail",
    css: `
      /* Full CSS support, add -webkit prefixes */
      * { -webkit-font-smoothing: antialiased; }
    `,
  },
  dark_mode: {
    name: "Dark Mode",
    css: `
      body { background-color: #1a1a2e !important; color: #e0e0e0 !important; }
      /* Invert images */
      img { filter: brightness(0.8) contrast(1.2); }
    `,
  },
};
```

### UI: Client dropdown

```
[ Gmail ▼ ] [ Desktop ▼ ] [ 🌙 Dark ]
┌──────────────┐
│ Generic      │
│ Gmail        │
│ Outlook      │
│ Apple Mail   │
└──────────────┘
```

Selecting a client applies the corresponding CSS overlay to the iframe.

---

## 7. Device Preview

### Width toggles

| Device | iframe width |
|--------|-------------|
| Desktop | 600px (email standard) |
| Tablet | 480px |
| Mobile | 320px |

### Implementation

```typescript
const [deviceWidth, setDeviceWidth] = useState(600);
// iframe wrapper: <div style={{ maxWidth: deviceWidth }}> <iframe> </div>
```

Buttons in the toolbar:
```
[ 🖥 Desktop ] [ 📱 Tablet ] [ 📱 Mobile ]
```

---

## 8. Dark Mode Toggle

- Adds CSS filter to simulate email in dark mode
- Inverts background/text colors while preserving brand colors
- Toggle switch in toolbar

```typescript
const darkModeCSS = `
  body { background: #1a1a2e !important; color: #e0e0e0 !important; }
  a { color: #66b2ff !important; }
  img { filter: brightness(0.9); }
  [style*="background-color"]:not(img):not(a) {
    filter: invert(0.85) hue-rotate(180deg);
  }
`;
```

---

## 9. Hot-Reload (Chokidar)

### Flow

```
amail/templates/*.html changed
  → Chokidar detects
  → WebSocket push to Vite dev server
  → useWebSocket hook triggers re-render
  → Preview iframe updates
```

### WebSocket server (proxy-server/websocket.js)

```javascript
const WebSocket = require("ws");
const chokidar = require("chokidar");

const wss = new WebSocket.Server({ port: 3001 });

chokidar.watch("../amail/templates/**/*.html").on("change", (path) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type: "template-changed", path }));
    }
  });
});
```

### useWebSocket hook

```typescript
function useWebSocket(onTemplateChange: (path: string) => void) {
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:3001");
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "template-changed") {
        onTemplateChange(msg.path);
      }
    };
    return () => ws.close();
  }, []);
}
```

---

## 10. Raw HTML Viewer

Collapsible panel at the bottom of the preview pane:

```
[ 📄 Show HTML ] ▼
┌──────────────────────────┐
│ <!DOCTYPE html>          │
│ <html lang="en">         │
│   <head>                 │
│     ...                  │
│ </html>                  │
└──────────────────────────┘
```

- Syntax highlighted (Prism.js or similar)
- "Copy to clipboard" button
- Automatically updates on re-render

---

## 11. Integration with Amail

### How the viewer connects to the amail project

```
amail-templates/
  ├── templates/ → symlink →  ../amail/templates/
  └── proxy-server/
        └── renderer.js  →  POST http://localhost:8000/api/v1/templates/render
                          →  (fallback: Python subprocess)
```

### Symlink setup

```bash
ln -s ../amail/templates templates
```

### Environment variables

| Var | Description |
|-----|-------------|
| `AMAIL_API_URL` | Amail server URL (default: `http://localhost:8000`) |
| `AMAIL_TEMPLATES_DIR` | Templates path (default: `./templates`) |
| `PROXY_PORT` | Express proxy port (default: `4000`) |
| `WS_PORT` | WebSocket port (default: `3001`) |
| `RENDER_MODE` | `api` (default) or `subprocess` |

---

## 12. API Contract (proxy server)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/templates` | List templates + metadata (proxied from amail or scanned from disk) |
| `POST` | `/api/render` | Render a template: `{ template, data }` → `{ html }` |
| `GET` | `/api/health` | Proxy server health |

### Proxy server handles:

1. **Template discovery** — reads template directory, parses Jinja2 extends/comments for metadata, or proxies to amail API
2. **Render requests** — forwards to amail API or runs Python subprocess
3. **File watching** — Chokidar WS notifications
4. **Static files** — serves Vite build in production

---

## 13. Future Enhancements

- **"Send Test Email" button** — calls amail `POST /api/v1/send` with current template + variables
- **A/B comparison** — two iframes side-by-side with different variable sets
- **Accessibility check** — automated color contrast warnings, missing alt text
- **CSS validation** — inline CSS warnings (deprecated props, missing mso prefixes)
- **Version history** — snapshot of template + variables, restore previous
- **Collaborative presets** — share preset JSON via URL
- **Spam score check** — basic spam trigger word detection
- **Preview history** — undo/redo for variable changes

---

## 14. Setup & Run

```bash
# Prerequisites
cd amail-templates
npm install

# Start proxy server (needed for render)
node proxy-server/index.js &

# Start Vite dev server
npm run dev

# Open browser
open http://localhost:5173
```

```json
// package.json (partial)
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "proxy": "node proxy-server/index.js",
    "dev:all": "concurrently \"npm run proxy\" \"npm run dev\""
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "typescript": "^5.6.0",
    "chokidar": "^4.0.0",
    "ws": "^8.18.0",
    "express": "^4.21.0",
    "concurrently": "^9.0.0"
  }
}
```

---

## 15. Implementation Order

```
Step 1: Scaffold Vite + React + Tailwind project
Step 2: Build Layout (sidebar + preview split)
Step 3: TemplateList component (read from disk or API)
Step 4: VariableEditor + VariableField (auto-generated from metadata)
Step 5: Proxy server with render endpoint
Step 6: PreviewPane with iframe
Step 7: Client simulations (Generic, Gmail, Outlook, Apple)
Step 8: Device toggle (Desktop/Mobile/Tablet)
Step 9: Dark mode toggle
Step 10: Raw HTML viewer
Step 11: Hot-reload via Chokidar + WebSocket
Step 12: Default variables + presets (localStorage)
Step 13: Symlink integration with amail/templates/
Step 14: Polish, error states, loading skeletons
```
