# Replay Viewer Performance

The supported first-pass target is Microsoft Edge on Windows. Budgets are:

- bundled replay usable within 5 seconds in the browser regression suite;
- 20,000 JSONL objects of roughly 80 bytes parsed within 1.5 seconds;
- 10,000 timeline lookups across 5,000 frames within 1 second;
- renderer chunk at or below the existing 560 kB minified budget.

Run:

```powershell
cd frontend
corepack yarn benchmark
corepack yarn test:browser
```

The synthetic parser input is substantially larger than the current demo
(86 frames and 581 events). These gates cover load and timeline CPU cost but do
not yet establish a memory ceiling or isolate Three.js scene rebuild cost.
Streaming, indexing, Web Workers, and renderer refactors remain unjustified
until those measurements exceed an agreed budget.
