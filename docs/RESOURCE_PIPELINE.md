# PYNIX GUI Resource Pipeline

## Status

Implementation batch in progress; verification pending.

## Goal

Application UI refers to logical resource names instead of scattering filesystem paths or
native image objects through the view tree.

## Values

```text
GUIImageResource(name, path)
GUIVectorResource(name, retainedScene | svgPath)
GUIResourceCatalog(images, vectors)
```

Convenience constructors:

```text
image_resource(name, path)
vector_resource(name, scene)
svg_resource(name, path)
resource_catalog(resources)
```

A catalog is installed on a GUIWindow. The backend resolves logical names during render.

Existing `image("name")` remains the image-view API. If the current resource catalog owns
that name, the logical resource wins; otherwise the backend may retain its platform-native
fallback behavior for compatibility.

`vector_icon("name", size)` resolves a retained Canvas 2D scene from the catalog and scales
it to the requested semantic icon size.

No native image handle, bundle URL or AppKit object is exposed as an application value.


Canvas image commands also resolve their `resource` through the installed image catalog
before treating it as a compatibility filesystem path. This keeps ordinary Image views and
Canvas images on one logical resource model.

SVG vector resources are rendered by the host backend (NSImage on macOS; QSvgRenderer on
Windows) while retained vector resources use the shared Canvas 2D scene model.
