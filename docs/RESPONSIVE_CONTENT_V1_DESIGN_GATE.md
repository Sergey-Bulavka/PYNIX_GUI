# Responsive Content V1 — design gate

## Scope
Product Gallery responds to semantic RESIZE events from Responsive Workspace V2.
Content width is calculated after sidebar and page insets. Breakpoints:
less than 680 logical points -> one card column and stacked workspace pairs;
680–1059 -> at most two card columns; 1060+ -> original card count.
Rerender on crossing the content topology boundary rather than every pixel.

## Behavior
- Overview, Start Here, Controls and Dashboard card grids adapt.
- Data, editor, forms, dashboard, IDE, settings and file manager workspace pairs
  choose row or column topology based on available content width.
- View leaf nodes keep their targets and controlled input state.
- Wide table, source editor, and retained Canvas have intrinsic minimum widths.
  They remain scrollable via the Gallery's outer scroll container rather than
  silently compressing columns or distorting drawing geometry.

## Boundaries
- Gallery-specific responsive composition, not a new generic layout engine.
- Wrapping existing controls and preserving focus across rerender still depend
  on the native backends; Mac visual acceptance required.
- Pixel parity and accessibility audit on Windows are not proven by CI.
- Responsive manual override remains as previously implemented.

## Acceptance
Check Overview, Controls, Forms, Data, Dashboard, IDE and File Manager at
wide / middle / narrow sizes, including text entry, navigation shortcuts,
sidebar transitions, retained Canvas, and viewport scrolling.
