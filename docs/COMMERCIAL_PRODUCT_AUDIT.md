# PYNIX GUI — Commercial Product Audit, 2026-10-09

## Product brief

PYNIX GUI is a native desktop UI toolkit using semantic immutable views,
a platform-independent layout engine, and AppKit / Qt backends. The goal is
not to mimic Qt's API or claim feature parity with Qt Widgets; it is to make
common desktop work easier to discover and implement.

## Audit categories and evidence

| Dimension | Finding | Evidence | Decision |
| --- | --- | --- | --- |
| Product discovery | The Gallery originally opened on an Overview whose features were descriptive but most capability blocks were not clickable. | `examples/showcase.py` previous Overview | Add real routes, a guide and visible discovery actions |
| First-use orientation | No guided step from building blocks to full app examples. | Previous ten-page NAVIGATION | Add `Start Here`, backed by existing real pages |
| Information architecture | Features and four apps shared a flat nav without explanatory journey. | Previous NAVIGATION and section headings | Preserve keyboard- and button-based navigation; provide route-based guide, defer sidebar categorization until responsive navigation is designed |
| Typography | AppKit glyph measurements previously clipped `Commands`. | Text Metrics V1 / Layout V2-V4 and native screenshot acceptance | Preserve measured layout and overflow options; avoid new font hacks |
| Window resizing | V4 prevented a crash for sizes below minimum but may retain last valid geometry. | V4 resize fix and tests | Do not present extreme-width behavior as complete responsive design |
| Native parity | CI exercises Mac/Windows/Linux test suites, not visual pixel comparison. | GitHub Actions matrix | Require Windows screenshots before stating visual parity |
| Public API discoverability | User could see widgets without understanding what tasks to build. | Old overview descriptions | Show capability-to-application pathways; keep all new CTAs functional |
| Accessible navigation | Sidebar uses native buttons, but keyboard traversal/assistive technology lacks a recorded audit. | Native UI implementations | Open a focused accessibility audit; do not claim compliance |
| Quality bar | Headless tests cannot prove commercial appearance. | Gallery validation tests | Supplement with native screenshot and resize acceptance |

## Implemented in this pass

- New guided entry page with a progression from building blocks to form
  controls and complete apps.
- Overview call-to-actions now open actual pages instead of relying on a
  modal description as the sole product entry point.
- Discovery actions are mapped explicitly to stable Page identifiers.
- Existing examples, navigation menu, demo contents and event semantics are
  retained. Additional tests ensure destinations exist and actions are real.

## Deliberate non-goals

- No wholesale palette replacement without user-reviewed visual designs;
  arbitrary styling would risk dark/light accessibility and native parity.
- No claims of WCAG or accessibility certification.
- No imitation of Qt Creator chrome or feature parity.
- No hidden responsive switching that would desynchronize the Gallery's
  application state during a native resize event.

## Manual acceptance

On macOS and Windows: check both light and dark themes, overview and guide,
every discovery CTA, ability to return via sidebar, keyboard focus, and
window resize at normal and narrow widths. Product screenshots should be
reviewed for text truncation, density and click target alignment.

## Recommended next milestones

1. Responsive sidebar/collapsible navigation with honest minimum window
   constraints and a user-tested mobile-like narrow desktop view.
2. Automated accessibility contracts for keyboard traversal, labels and
   meaningful focus semantics.
3. Screenshot baselines with platform-native font metrics and DPI.
4. Cross-platform visual review of a real PYNIX GUI application before
   advancing the public product stability claim.
