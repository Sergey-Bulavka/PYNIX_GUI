# PYNIX GUI Resource Pipeline

## Status

Implementation batch in progress; verification pending.

## Goal

Application UI refers to logical resource names instead of scattering filesystem paths or
native image objects through the view tree.

## Values

```text
GUIImageResource(name, path)
GUIVectorResource(name, GUICanvasScene)
GUIResourceCatalog(images, vectors)
```

Convenience constructors:

```text
image_resource(name, path)
vector_resource(name, scene)
resource_catalog(resources)
```

A catalog is installed on a GUIWindow. The backend resolves logical names during render.

Existing `image("name")` remains the image-view API. If the current resource catalog owns
that name, the logical resource wins; otherwise the backend may retain its platform-native
fallback behavior for compatibility.

`vector_icon("name", size)` resolves a retained Canvas 2D scene from the catalog and scales
it to the requested semantic icon size.

No native image handle, bundle URL or AppKit object is exposed as an application value.
