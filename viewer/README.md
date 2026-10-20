# Browser viewer

Inspect the cabinet geometry and moving parts in a local browser.

Start from the project directory:

```sh
cd viewer
npm start
```

Open http://127.0.0.1:8765. Drag to orbit, scroll to zoom, and right-drag to pan. Camera buttons and the part selector also work with the keyboard. On phones, open the controls below the model.

Extend the toilet and dog platform independently. The toilet door opens when the tray moves. Hide front panels or the countertop to inspect the interior. Click a part, or select it from the list, to see its dimensions. The separation slider spreads parts for inspection. Reset restores the initial view.

The CAD countertop remains uncut. The sink outline marks reserved component space and can be seen through the top. Component dimensions, 18 inch depth, hardware and safe loads remain provisional.

## Update the model

After editing the approved CAD parameters, regenerate the model and browser bundle:

```sh
npm run rebuild
```

For interface-only changes, run `npm run build`. On a fresh checkout, install the pinned JavaScript dependencies with `npm ci`. CAD generation also needs the Python environment described in [the project README](../README.md).

All viewer source files and JavaScript dependencies live in this directory. Source files are `viewer.html`, `viewer.css`, `viewer.js`, `export_viewer.py`, `build_viewer.mjs` and `serve_viewer.py`. Generated browser assets live in `dist/`. The viewer uses local assets and serves only that directory on loopback.

Run `npm test` while the server is running to verify loading, selection, orientation, motion, visibility, camera presets and mobile layout. Browser screenshots are saved under `dist/qa-*.png`. Tests use the installed Chromium; set `CABINET_BROWSER_PATH` for another Chromium executable.

## Page plan

Goal: inspect the cabinet in three dimensions. Audience: the cabinet owner and fabricator reviewing the preliminary layout. Content: CAD geometry, motion controls, visibility, part dimensions, downloads and concept status. Open decisions: component approval, finished depth, plumbing, hardware and structural validation.
