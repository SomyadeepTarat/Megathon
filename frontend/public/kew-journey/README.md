# Kew introduction assets

`scene.js` adapts the city, landmarks, destination home, eco upgrades and camera
path from `tmp/kew-reference/dist/app.js`. It exposes `createJourneyScene(canvas)`
with `resize`, `render(progress)` and `dispose` methods. The React controller is
`components/home-journey.tsx`; scoped presentation is in `home-journey.css`.

The supplied Three.js 0.180.0 modules are served locally from `vendor/`, with their
original license. No CDN or prototype dashboard/storage code is used.

The Overview route mounts the introduction before the existing workspace. Other
routes retain the original workspace. Scrolling uses native document scrolling;
only camera progress is eased. Frames stop when progress settles, the section
leaves the viewport, or the document is hidden. The scene is loaded on demand.
Unmounting releases observers, listeners, animation frames, geometries,
materials, instanced meshes and the renderer/context.

Reduced motion skips WebGL initialization and shows the existing home illustration
in a short introduction. Initialization or context failure uses the same fallback.
Skip and replay move immediately and place keyboard focus on the destination.
Eco callouts are illustrative and do not feed assessment or savings calculations.

Run locally from `frontend`: `npm run dev`.
Checks: `npm run typecheck`, `npm run build`, `npm test` (Node 22.6+ for the test
script's TypeScript stripping flag).

Manual checks: scroll through the city/home/eco/landing phases at desktop and
mobile sizes; use Skip and Replay; open Assessment and return to Overview; enable
OS reduced motion; test with WebGL disabled; hide the tab and scroll past the
introduction to confirm idle rendering. The last two device configurations should
be checked on the target browser/hardware before release.
