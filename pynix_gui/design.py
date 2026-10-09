# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""PYNIX Standard design-system tokens."""

from dataclasses import dataclass


SPACING = {
    "space0": 0,
    "space1": 4,
    "space2": 8,
    "space3": 12,
    "space4": 16,
    "space5": 24,
    "space6": 32,
    "space7": 48,
}

RADII = {
    "radius0": 0,
    "radius1": 4,
    "radius2": 8,
    "radius3": 12,
    "radius4": 16,
    "radiusRound": 999,
}

ELEVATION = {
    "flat": 0,
    "raised": 1,
    "floating": 2,
    "overlay": 3,
}

LINES = {
    "hairline": 1,
    "thin": 1,
    "strong": 2,
    "focus": 2,
}

CONTROL_METRICS = {
    "compactControl": 28,
    "standardControl": 32,
    "comfortableControl": 40,
    "toolbar": 40,
    "statusBar": 28,
}

ICON_METRICS = {
    "iconSmall": 14,
    "iconStandard": 16,
    "iconMedium": 20,
    "iconLarge": 24,
    "iconHero": 32,
}

TYPOGRAPHY = {
    "caption": (12.0, "regular"),
    "overline": (11.0, "semibold"),
    "body": (13.0, "regular"),
    "bodyStrong": (13.0, "semibold"),
    "label": (13.0, "medium"),
    "subheading": (14.0, "semibold"),
    "titleSmall": (15.0, "semibold"),
    "title": (18.0, "semibold"),
    "heading": (20.0, "bold"),
    "titleLarge": (24.0, "bold"),
    "display": (30.0, "bold"),
    "metric": (28.0, "bold"),
    "code": (13.0, "monospace"),
}

# Canonical PYNIX Standard palettes. Values are sRGB hex strings.
LIGHT = {
    "background": "#F5F6F8",
    "surface": "#FFFFFF",
    "surfaceRaised": "#FFFFFF",
    "surfaceSunken": "#F0F2F5",
    "surfaceSelected": "#DCEBFF",
    "surfaceHover": "#EEF4FF",
    "surfacePressed": "#D3E4FF",
    "textPrimary": "#16181D",
    "textSecondary": "#4A4F59",
    "textMuted": "#777D87",
    "textDisabled": "#A8ADB5",
    "textOnAccent": "#FFFFFF",
    "accent": "#0A6EEB",
    "accentHover": "#095FCB",
    "accentPressed": "#084FA9",
    "accentMuted": "#BFD8FA",
    "border": "#D3D7DE",
    "borderStrong": "#AEB4BE",
    "separator": "#E1E4E9",
    "focus": "#0A6EEB",
    "success": "#238636",
    "warning": "#B7791F",
    "error": "#D1242F",
    "info": "#0969DA",
    "successMuted": "#E9F7ED",
    "warningMuted": "#FFF4D6",
    "errorMuted": "#FDECEE",
    "infoMuted": "#E8F2FF",
    "accentSubtle": "#EEF5FF",
    "surfaceOverlay": "#FFFFFF",
}

DARK = {
    "background": "#17191D",
    "surface": "#202328",
    "surfaceRaised": "#272B31",
    "surfaceSunken": "#15171A",
    "surfaceSelected": "#153A66",
    "surfaceHover": "#252E3A",
    "surfacePressed": "#1F3956",
    "textPrimary": "#F2F4F7",
    "textSecondary": "#C8CDD5",
    "textMuted": "#9299A4",
    "textDisabled": "#626873",
    "textOnAccent": "#FFFFFF",
    "accent": "#4C9AFF",
    "accentHover": "#6AADFF",
    "accentPressed": "#2F82E8",
    "accentMuted": "#274A70",
    "border": "#3A3F47",
    "borderStrong": "#555C67",
    "separator": "#30343A",
    "focus": "#69A9FF",
    "success": "#3FB950",
    "warning": "#D29922",
    "error": "#F85149",
    "info": "#58A6FF",
    "successMuted": "#183C24",
    "warningMuted": "#433618",
    "errorMuted": "#442326",
    "infoMuted": "#18344F",
    "accentSubtle": "#1E2D41",
    "surfaceOverlay": "#30343B",
}

THEMES = {"light", "dark", "system"}
COLOR_ROLES = frozenset(LIGHT)
TEXT_ROLES = frozenset(TYPOGRAPHY)

SURFACE_COLOR_ROLES = {
    "app": "background",
    "panel": "surface",
    "sidebar": "surfaceRaised",
    "workspace": "background",
    "toolPanel": "surface",
    "dialog": "surfaceRaised",
    "group": "surface",
    "settings": "surface",
    "section": "surface",
    "toolbar": "surfaceRaised",
    "status": "surfaceRaised",
    "surfaceSunken": "surfaceSunken",
    "separator": "separator",
    "selected": "surfaceSelected",
    "surfaceSelected": "surfaceSelected",
    "card": "surfaceRaised",
    "hero": "accentSubtle",
    "navigation": "surfaceRaised",
    "mutedSurface": "surfaceSunken",
    "successSurface": "successMuted",
    "warningSurface": "warningMuted",
    "dangerSurface": "errorMuted",
    "infoSurface": "infoMuted",
    "accentSurface": "accentSubtle",
    "overlay": "surfaceOverlay",
}

BUTTON_VISUALS = {
    "primary": {
        "surface": "accent",
        "text": "textOnAccent",
        "bordered": True,
    },
    "secondary": {
        "surface": "surfaceRaised",
        "text": "textPrimary",
        "bordered": True,
    },
    "quiet": {
        "surface": None,
        "text": "textPrimary",
        "bordered": False,
    },
    "danger": {
        "surface": "error",
        "text": "textOnAccent",
        "bordered": True,
    },
}


def surface_color_role(role: str):
    return SURFACE_COLOR_ROLES.get(role, role)


def button_visual(role: str):
    return BUTTON_VISUALS[role]


def palette(theme: str):
    if theme == "light":
        return LIGHT
    if theme == "dark":
        return DARK
    raise ValueError("system theme must be resolved by host backend")


def rgb(hex_value: str):
    value = hex_value.lstrip("#")
    if len(value) != 6:
        raise ValueError("design color must be #RRGGBB")
    return tuple(int(value[i:i+2], 16) / 255.0 for i in (0, 2, 4))
