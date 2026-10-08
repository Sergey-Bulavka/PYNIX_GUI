# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Logical application resource catalog."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError
from .canvas import GUICanvasScene


def _name(value, label):
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-013", f"{label} must be a non-empty String.")
    return value


@dataclass(frozen=True, slots=True)
class GUIImageResource:
    name: str
    path: str

    def __post_init__(self):
        _name(self.name, "GUI image resource name")
        _name(self.path, "GUI image resource path")


@dataclass(frozen=True, slots=True)
class GUIVectorResource:
    name: str
    scene: GUICanvasScene

    def __post_init__(self):
        _name(self.name, "GUI vector resource name")
        if not isinstance(self.scene, GUICanvasScene):
            raise GUIError("PYNIX-GUI-013", "GUI vector resource scene is invalid.")


@dataclass(frozen=True, slots=True)
class GUIResourceCatalog:
    images: tuple[GUIImageResource, ...] = ()
    vectors: tuple[GUIVectorResource, ...] = ()

    def __post_init__(self):
        if type(self.images) is not tuple or any(
            not isinstance(value, GUIImageResource) for value in self.images
        ):
            raise GUIError("PYNIX-GUI-013", "GUI image resources are invalid.")
        if type(self.vectors) is not tuple or any(
            not isinstance(value, GUIVectorResource) for value in self.vectors
        ):
            raise GUIError("PYNIX-GUI-013", "GUI vector resources are invalid.")

        names = [value.name for value in self.images] + [
            value.name for value in self.vectors
        ]
        if len(set(names)) != len(names):
            raise GUIError("PYNIX-GUI-013", "GUI resource names must be globally unique.")

    def image_path(self, name: str):
        for resource in self.images:
            if resource.name == name:
                return resource.path
        return None

    def vector_scene(self, name: str):
        for resource in self.vectors:
            if resource.name == name:
                return resource.scene
        return None

    def contains(self, name: str) -> bool:
        return self.image_path(name) is not None or self.vector_scene(name) is not None


def image_resource(name: str, path: str) -> GUIImageResource:
    return GUIImageResource(name, path)


def vector_resource(name: str, scene: GUICanvasScene) -> GUIVectorResource:
    return GUIVectorResource(name, scene)


def resource_catalog(resources) -> GUIResourceCatalog:
    if isinstance(resources, (str, bytes)) or not isinstance(resources, Sequence):
        raise GUIError("PYNIX-GUI-013", "GUI resources must be a sequence.")

    images = []
    vectors = []
    for resource in resources:
        if isinstance(resource, GUIImageResource):
            images.append(resource)
        elif isinstance(resource, GUIVectorResource):
            vectors.append(resource)
        else:
            raise GUIError("PYNIX-GUI-013", "GUI resource value is invalid.")

    return GUIResourceCatalog(tuple(images), tuple(vectors))
