# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""PYNIX GUI Product Gallery — commercial showcase and capability browser."""

from pynix_gui import (
    GUIRuntime,
    alert,
    badge,
    button,
    button_group,
    canvas,
    canvas_ellipse,
    canvas_line,
    canvas_rect,
    canvas_scene,
    canvas_text,
    card,
    check_box,
    column,
    combo_box,
    empty_state,
    fill,
    form_row,
    form_section,
    grid,
    hero,
    max_size,
    menu,
    menu_bar,
    menu_item,
    metric_card,
    min_size,
    navigation_item,
    navigation_sidebar,
    padding,
    progress_bar,
    property_row,
    radio_button,
    rich_editor,
    row,
    scroll,
    search_field,
    section_header,
    shortcut,
    slider,
    table,
    table_column,
    table_row,
    text,
    text_area,
    text_field,
    text_span,
    theme,
    tree,
    tree_node,
)
from pynix_gui import dialog, dialog_action
from pynix_gui.backends import default_backend


NAVIGATION = (
    ("overview", "Overview"),
    ("start", "Start Here"),
    ("controls", "Controls"),
    ("data", "Data"),
    ("editor", "Rich Editor"),
    ("canvas", "Canvas 2D"),
    ("forms", "Forms"),
    ("dashboard", "Dashboard App"),
    ("ide", "IDE App"),
    ("settings", "Settings App"),
    ("files", "File Manager"),
)

TREE = [
    tree_node(
        "src",
        "src",
        [
            tree_node("main", "main.pnx"),
            tree_node(
                "ui",
                "ui",
                [
                    tree_node("gallery", "gallery.pnx"),
                    tree_node("components", "components.pnx"),
                ],
            ),
        ],
    ),
    tree_node("assets", "assets"),
    tree_node("tests", "tests"),
]

COLUMNS = [
    table_column("name", "Component", 220),
    table_column("category", "Category", 150),
    table_column("state", "State", 120),
]

ROWS = [
    table_row("editor", ["Rich Editor", "Advanced", "Accepted"]),
    table_row("canvas", ["Canvas 2D", "Advanced", "Accepted"]),
    table_row("tree", ["Tree", "Data", "Accepted"]),
    table_row("table", ["Table", "Data", "Accepted"]),
    table_row("dialog", ["Dialog", "Commands", "Accepted"]),
]

SOURCE = """function buildDashboard()
    return GUI.column([
        GUI.heading("Workspace"),
        GUI.card("Traffic", chart),
        GUI.table("sessions", columns, rows)
    ])
"""


def source_spans(value):
    spans = []
    for token, role in (
        ("function", "keyword"),
        ("return", "keyword"),
        ("GUI", "type"),
        ('"Workspace"', "string"),
        ('"Traffic"', "string"),
        ('"sessions"', "string"),
    ):
        start = value.find(token)
        if start >= 0:
            spans.append(text_span(start, start + len(token), role))
    return spans


def product_scene():
    return canvas_scene(
        760,
        360,
        [
            canvas_rect(12, 12, 736, 336, fill="surface", stroke="borderStrong"),
            canvas_text(42, 50, "Realtime workspace", role="titleLarge"),
            canvas_text(42, 82, "Retained Canvas 2D + semantic hit targets", role="body"),
            canvas_line(42, 104, 710, 104, stroke="separator"),
            canvas_rect(
                42,
                135,
                210,
                150,
                fill="surfaceSelected",
                stroke="accent",
                hit_target="canvas-card",
            ),
            canvas_text(68, 176, "24.8k", role="titleLarge"),
            canvas_text(68, 208, "active sessions", role="body"),
            canvas_ellipse(
                320,
                135,
                150,
                150,
                fill="accentMuted",
                stroke="accent",
                line_width=2,
                hit_target="canvas-circle",
            ),
            canvas_text(320, 135, "72%", role="title", width=150, height=150, align="center", valign="center"),
            canvas_rect(
                530,
                160,
                160,
                28,
                fill="success",
                stroke="success",
                hit_target="canvas-status",
            ),
            canvas_text(530, 160, "HEALTHY", role="label", color="textOnAccent", width=160, height=28, align="center", valign="center"),
        ],
    )


# These are real gallery routes, not decorative buttons. Each target opens
# a working page powered by the same public PYNIX GUI component API.
DISCOVERY_ROUTES = {
    "discover-start": "start",
    "discover-controls": "controls",
    "discover-controls-step": "controls",
    "discover-data": "data",
    "discover-editor": "editor",
    "discover-canvas": "canvas",
    "discover-forms": "forms",
    "discover-dashboard": "dashboard",
    "discover-dashboard-card": "dashboard",
    "discover-ide": "ide",
    "discover-settings": "settings",
    "discover-files": "files",
}


def getting_started_page():
    return column([
        hero(
            "From an idea to a native desktop application.",
            "Explore the building blocks, combine them into screens, and see "
            "the same semantic interface running through AppKit and Qt.",
            [
                button("discover-controls", "Explore components", "primary"),
                button("discover-dashboard", "Open an application example"),
            ],
        ),
        section_header(
            "Three steps to your first interface",
            "Each step opens a working Product Gallery screen.",
        ),
        grid(3, [
            card(
                "01 · Build",
                column([
                    text("Compose with Row, Column, Grid, Panel and Card.",
                         "body", overflow="wrap"),
                    button("discover-controls-step", "Explore controls"),
                ], 12),
                "Build layouts using semantic views.",
            ),
            card(
                "02 · Connect",
                column([
                    text("Use inputs, validation-oriented forms and "
                         "normalized interaction events.", "body", overflow="wrap"),
                    button("discover-forms", "Open forms"),
                ], 12),
                "Handle user input with native controls.",
            ),
            card(
                "03 · Ship",
                column([
                    text("Combine data, editing and drawing in desktop "
                         "application layouts.", "body", overflow="wrap"),
                    button("discover-ide", "See the IDE example"),
                ], 12),
                "Inspect complete application examples.",
            ),
        ], 16, 16),
        section_header(
            "Explore by capability",
            "Choose a real demonstration rather than reading a feature list.",
        ),
        grid(2, [
            card(
                "Structured data",
                button("discover-data", "Explore Tree & Table", "primary"),
                "Selection, expansion and normalized data events.",
            ),
            card(
                "Rich editing",
                button("discover-editor", "Explore the editor", "primary"),
                "Controlled source text, selections and semantic spans.",
            ),
            card(
                "Canvas 2D",
                button("discover-canvas", "Open interactive canvas", "primary"),
                "Retained drawing, transforms and semantic hit testing.",
            ),
            card(
                "Desktop workflows",
                button("discover-files", "Open File Manager", "primary"),
                "Inspect a composed navigation and data interface.",
            ),
        ], 16, 16),
        alert(
            "Complex inside. Simple outside.",
            "PYNIX GUI provides semantic interface primitives; native "
            "implementation details remain inside the platform backends.",
            "info",
        ),
    ], 20)


def overview_page():
    metrics = [
        metric_card(
            "Core surfaces",
            "30+",
            "Composable semantic building blocks",
            badge("Stable", "success"),
        ),
        metric_card(
            "Advanced systems",
            "5",
            "Tree/Table · Dock · Canvas · Editor",
            badge("Native", "accent"),
        ),
        metric_card(
            "Supported themes",
            "3",
            "System · Light · Dark",
            badge("Ready", "info"),
        ),
    ]

    capability_cards = [
        card(
            "Desktop foundation",
            column([
                property_row("Layout", "Row · Column · Grid · Stack"),
                property_row("Surfaces", "Cards · Panels · Scroll · Split"),
                property_row("Commands", "Menus · Dialogs · Shortcuts"),
            ], 10),
            "Predictable geometry and native lifecycle.",
        ),
        card(
            "Advanced workspace",
            column([
                property_row("Data", "Tree · Table"),
                property_row("Content", "Rich Editor · Canvas 2D"),
                property_row("Interaction", "Drag · Drop · Docking"),
            ], 10),
            "The pieces needed for serious desktop software.",
        ),
    ]

    return column([
        hero(
            "Build polished desktop software with less ceremony.",
            "PYNIX GUI combines semantic design, deterministic layout and native backends behind a compact declarative API.",
            [
                button("discover-start", "Get started", "primary"),
                button("discover-dashboard", "See application examples"),
            ],
        ),
        grid(3, metrics, 16, 16),
        section_header(
            "What you can build",
            "The Gallery exposes the product as a toolkit, not as an engineering test fixture.",
            badge("Commercial Product Pass", "accent"),
        ),
        grid(2, capability_cards, 16, 16),
        section_header(
            "Try it yourself",
            "Each action opens an interactive demonstration.",
        ),
        grid(3, [
            card(
                "UI building blocks",
                button("discover-controls", "Explore controls", "primary"),
                "Buttons, input, selection and state.",
            ),
            card(
                "Advanced workspaces",
                button("discover-editor", "Explore rich editor", "primary"),
                "Editing, data views and native interaction.",
            ),
            card(
                "Complete applications",
                button("discover-dashboard-card", "View dashboard", "primary"),
                "See components working together.",
            ),
        ], 16, 16),
        alert(
            "Complex inside. Simple outside.",
            "Application code works with semantic PYNIX values while AppKit and Qt remain private implementation details.",
            "info",
        ),
    ], 20)


def controls_page(state):
    return column([
        section_header(
            "Controls",
            "Production controls with semantic states and commercial defaults.",
            badge("Interactive", "success"),
        ),
        grid(2, [
            card(
                "Buttons",
                column([
                    button_group([
                        button("primary-action", "Primary", "primary"),
                        button("secondary-action", "Secondary"),
                        button("quiet-action", "Quiet", "quiet"),
                        button("danger-action", "Danger", "danger"),
                    ]),
                    text("Primary, secondary, quiet and destructive intent.", "caption"),
                ], 10),
                "Intent is semantic; native backend styling stays internal.",
            ),
            card(
                "Input",
                column([
                    search_field("gallery-search", state["search"], "Search components"),
                    text_field("display-name", state["name"], "Display name"),
                    text_area("notes", state["notes"]),
                ], 10),
                "Controlled text inputs and multiline editing.",
            ),
            card(
                "Selection",
                column([
                    check_box("telemetry", "Enable telemetry", state["checked"]),
                    radio_button("channel-stable", "Stable channel", True),
                    combo_box("appearance", ["System", "Light", "Dark"], state["appearance"]),
                ], 10),
                "Check, radio and selection controls normalize events.",
            ),
            card(
                "Range & status",
                column([
                    text("Workspace scale", "label"),
                    slider("scale", state["scale"], 0, 100),
                    progress_bar(state["scale"], 0, 100),
                    row([
                        badge("Healthy", "success"),
                        badge("Preview", "warning"),
                        badge("Offline", "danger"),
                        badge("Info", "info"),
                    ], 8),
                ], 10),
                "Range controls pair naturally with semantic status components.",
            ),
        ], 16, 16),
        alert(
            "Focus is preserved across controlled rerenders.",
            "Rich text and ordinary text controls keep interaction continuity when application state updates.",
            "success",
        ),
    ], 18)


def data_page(state):
    return column([
        section_header(
            "Data views",
            "Stable identities, selection and keyboard behavior for structured information.",
            badge("ADV-02", "accent"),
        ),
        row([
            fill(card(
                "Project Tree",
                min_size(
                    tree(
                        "gallery-tree",
                        TREE,
                        expanded_ids=["src", "ui"],
                        selected_id=state["tree_selected"],
                    ),
                    300,
                    360,
                ),
                "Hierarchical navigation with controlled expansion.",
            )),
            fill(card(
                "Component Table",
                min_size(
                    table(
                        "gallery-table",
                        COLUMNS,
                        ROWS,
                        selected_id=state["table_selected"],
                    ),
                    520,
                    360,
                ),
                "Explicit columns remain readable and selectable.",
            )),
        ], 16),
        card(
            "Selected state",
            row([
                badge("Tree: " + str(state["tree_selected"]), "neutral"),
                badge("Table: " + str(state["table_selected"]), "neutral"),
            ], 8),
            "Selection is application state, not an opaque native object.",
        ),
    ], 18)


def editor_page(state):
    return column([
        section_header(
            "Rich Editor",
            "Controlled source text with semantic spans and native editing behavior.",
            badge("ADV-05", "accent"),
        ),
        row([
            fill(card(
                "Source",
                min_size(
                    rich_editor(
                        "gallery-editor",
                        state["source"],
                        state["selection_start"],
                        state["selection_end"],
                        source_spans(state["source"]),
                    ),
                    620,
                    480,
                ),
                "Continuous typing, Backspace, native selection and scrolling.",
            )),
            max_size(
                card(
                    "Editor contract",
                    column([
                        property_row("Text", "Controlled"),
                        property_row("Selection", "Controlled"),
                        property_row("Styling", "Semantic spans"),
                        property_row("Undo", "Native"),
                        property_row("Find", "Native"),
                        alert(
                            "Focus preserved",
                            "Controlled rerender keeps the active caret.",
                            "success",
                        ),
                    ], 12),
                    "No native NSTextView or QPlainTextEdit leaks into application code.",
                ),
                520,
                900,
            ),
        ], 16),
    ], 18)


def canvas_page():
    return column([
        section_header(
            "Canvas 2D",
            "Retained drawing commands, transforms and semantic hit testing.",
            badge("ADV-04", "accent"),
        ),
        card(
            "Interactive retained scene",
            min_size(canvas("gallery-canvas", product_scene()), 760, 420),
            "Click the metric card, circle or health bar. Events return semantic targets rather than coordinates.",
        ),
        row([
            badge("Paths", "neutral"),
            badge("Text", "neutral"),
            badge("Images", "neutral"),
            badge("Clip", "neutral"),
            badge("Transform", "neutral"),
            badge("Hit targets", "success"),
        ], 8),
    ], 18)


def forms_page(state):
    return column([
        section_header(
            "Forms & settings",
            "High-level composition for application settings and account flows.",
            badge("Composition", "accent"),
        ),
        row([
            fill(form_section(
                "Profile",
                [
                    form_row(
                        "Display name",
                        text_field("profile-name", state["name"], "Your name"),
                        "Shown in collaborative workspaces.",
                    ),
                    form_row(
                        "Appearance",
                        combo_box("profile-theme", ["System", "Light", "Dark"], state["appearance"]),
                        "System follows the host operating system.",
                    ),
                    form_row(
                        "Search",
                        search_field("profile-search", state["search"], "Filter preferences"),
                    ),
                ],
                "A complete semantic form without platform-specific layout code.",
            )),
            max_size(
                card(
                    "Workspace",
                    column([
                        property_row("Autosave", "Enabled", "Every 30 seconds"),
                        property_row("Cloud sync", "Connected"),
                        property_row("Channel", "Stable"),
                        alert(
                            "All changes saved",
                            "Settings are synchronized with the current workspace.",
                            "success",
                        ),
                    ], 12),
                    "Dense property presentation for inspectors and settings.",
                ),
                540,
                900,
            ),
        ], 16),
        empty_state(
            "No additional integrations",
            "Connected services and plugin surfaces can appear here when available.",
            button("open-dialog", "Learn more", "primary"),
        ),
    ], 18)


def dashboard_page():
    project_rows = [
        table_row("alpha", ["Alpha Workspace", "Dashboard", "Healthy"]),
        table_row("beta", ["Beta Console", "Operations", "Healthy"]),
        table_row("gamma", ["Gamma Studio", "Creative", "Preview"]),
    ]
    return column([
        section_header(
            "Application example",
            "A realistic operations dashboard assembled entirely from PYNIX GUI primitives and commercial components.",
            badge("Reference UI", "success"),
        ),
        hero(
            "Operations Console",
            "Monitor workspaces, inspect health and act on the same semantic event model used by every other PYNIX GUI application.",
            [
                button("new-workspace", "New workspace", "primary"),
                button("open-dialog", "Share"),
            ],
        ),
        grid(3, [
            metric_card("Active users", "24.8k", "+12.4% this month", badge("+12.4%", "success")),
            metric_card("Latency", "38 ms", "Global median", badge("Good", "success")),
            metric_card("Incidents", "2", "One requires review", badge("Review", "warning")),
        ], 16, 16),
        row([
            fill(card(
                "Workspace activity",
                min_size(canvas("example-canvas", product_scene()), 620, 300),
                "A Canvas module can live beside ordinary controls and data views.",
            )),
            max_size(card(
                "Environment",
                column([
                    property_row("Region", "EU Central"),
                    property_row("Runtime", "PYNIX 1.x"),
                    property_row("GUI", "0.1.6-dev"),
                    alert("Healthy", "All core services are operational.", "success"),
                ], 12),
                "Inspector-style application surface.",
            ), 360, 900),
        ], 16),
        card(
            "Projects",
            min_size(
                table(
                    "example-table",
                    [
                        table_column("project", "Project", 260),
                        table_column("kind", "Type", 180),
                        table_column("health", "Health", 140),
                    ],
                    project_rows,
                    selected_id="alpha",
                ),
                620,
                220,
            ),
            "Tables belong inside finished application layouts, not isolated demos.",
        ),
    ], 18)


def ide_app_page(state):
    return column([
        section_header(
            "IDE application",
            "A complete developer workspace assembled from Tree, Rich Editor, Table and commands.",
            badge("Reference UI", "success"),
        ),
        hero(
            "PYNIX Studio",
            "Project navigation, source editing and diagnostics in one semantic desktop workspace.",
            [
                button("ide-run", "Run", "primary"),
                button("open-dialog", "Command palette"),
            ],
        ),
        row([
            max_size(card(
                "Explorer",
                min_size(
                    tree(
                        "ide-tree",
                        TREE,
                        expanded_ids=["src", "ui"],
                        selected_id=state["tree_selected"],
                    ),
                    260,
                    500,
                ),
                "Keyboard-navigable project structure.",
            ), 320, 900),
            fill(card(
                "main.pnx",
                min_size(
                    rich_editor(
                        "ide-editor",
                        state["source"],
                        state["selection_start"],
                        state["selection_end"],
                        source_spans(state["source"]),
                    ),
                    600,
                    500,
                ),
                "Native editing behavior behind a controlled semantic value.",
            )),
        ], 16),
        card(
            "Problems",
            min_size(
                table(
                    "ide-problems",
                    [
                        table_column("severity", "Severity", 120),
                        table_column("message", "Message", 460),
                        table_column("file", "File", 180),
                    ],
                    [
                        table_row("p1", ["Info", "Workspace is ready", "main.pnx"]),
                        table_row("p2", ["Hint", "Commercial Product Pass active", "gallery.pnx"]),
                    ],
                    selected_id="p1",
                ),
                700,
                170,
            ),
            "Diagnostics and tooling output fit the same table contract.",
        ),
    ], 18)


def settings_app_page(state):
    return column([
        section_header(
            "Settings application",
            "A polished preferences surface using forms, property rows, alerts and semantic status.",
            badge("Reference UI", "success"),
        ),
        hero(
            "Workspace Settings",
            "Manage appearance, identity and synchronization without hand-built platform layout.",
            [button("settings-save", "Save changes", "primary")],
        ),
        row([
            fill(form_section(
                "General",
                [
                    form_row(
                        "Display name",
                        text_field("settings-name", state["name"], "Display name"),
                    ),
                    form_row(
                        "Appearance",
                        combo_box("settings-theme", ["System", "Light", "Dark"], state["appearance"]),
                    ),
                    form_row(
                        "Search preferences",
                        search_field("settings-search", state["search"], "Search settings"),
                    ),
                    form_row(
                        "Telemetry",
                        check_box("settings-telemetry", "Share anonymous diagnostics", state["checked"]),
                    ),
                ],
                "Core workspace preferences.",
            )),
            max_size(card(
                "Account",
                column([
                    property_row("Plan", "Developer"),
                    property_row("Sync", "Connected"),
                    property_row("Region", "EU Central"),
                    alert(
                        "Protected",
                        "Application-facing code never receives native backend handles.",
                        "info",
                    ),
                ], 12),
                "Semantic application state.",
            ), 540, 900),
        ], 16),
    ], 18)


def file_manager_page(state):
    file_rows = [
        table_row("f-main", ["main.pnx", "PYNIX", "4 KB"]),
        table_row("f-gallery", ["gallery.pnx", "PYNIX", "11 KB"]),
        table_row("f-readme", ["README.md", "Markdown", "6 KB"]),
        table_row("f-assets", ["assets", "Folder", "—"]),
    ]
    return column([
        section_header(
            "File manager",
            "Navigation, search, structured data and actions composed into a familiar desktop workflow.",
            badge("Reference UI", "success"),
        ),
        row([
            search_field("files-search", state["search"], "Search files"),
            fill(text("Project / src", "caption")),
            button("file-new", "New", "primary"),
            button("file-more", "More"),
        ], 10),
        row([
            max_size(card(
                "Folders",
                min_size(
                    tree(
                        "files-tree",
                        TREE,
                        expanded_ids=["src", "ui"],
                        selected_id=state["tree_selected"],
                    ),
                    260,
                    480,
                ),
                "Stable hierarchical identities.",
            ), 320, 900),
            fill(card(
                "Files",
                min_size(
                    table(
                        "files-table",
                        [
                            table_column("name", "Name", 300),
                            table_column("kind", "Kind", 180),
                            table_column("size", "Size", 120),
                        ],
                        file_rows,
                        selected_id="f-main",
                    ),
                    700,
                    480,
                ),
                "Rows, columns and selection stay semantic across native backends.",
            )),
        ], 16),
        row([
            badge("4 items", "neutral"),
            badge("Synced", "success"),
            fill(text("PYNIX project", "caption")),
        ], 8),
    ], 18)


def page_view(page, state):
    if page == "start":
        return getting_started_page()
    if page == "controls":
        return controls_page(state)
    if page == "data":
        return data_page(state)
    if page == "editor":
        return editor_page(state)
    if page == "canvas":
        return canvas_page()
    if page == "forms":
        return forms_page(state)
    if page == "dashboard":
        return dashboard_page()
    if page == "ide":
        return ide_app_page(state)
    if page == "settings":
        return settings_app_page(state)
    if page == "files":
        return file_manager_page(state)
    return overview_page()


def build(page, state):
    sidebar = navigation_sidebar(
        "PYNIX GUI",
        [
            navigation_item("nav-" + key, label, page == key)
            for key, label in NAVIGATION
        ],
        footer=column([
            badge("0.1.6-dev", "accent"),
            text("Commercial Product Pass", "caption"),
        ], 6),
    )

    content = scroll(
        padding(
            column([
                page_view(page, state),
                text("PYNIX Standard · semantic by default", "caption"),
            ], 16),
            24,
        )
    )

    return theme(
        row([
            max_size(min_size(sidebar, 230, 560), 270, 2000),
            fill(content),
        ], 0),
        "system",
    )


def main():
    backend = default_backend()
    if backend is None:
        raise SystemExit("No native PYNIX GUI backend is available on this platform.")

    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI backend is unavailable.")

    window = runtime.open("PYNIX GUI — Product Gallery", 1440, 900)
    window.set_menu_bar(
        menu_bar([
            menu(
                "File",
                [
                    menu_item("nav-overview", "Overview", shortcut("1", ["primary"])),
                    menu_item("open-dialog", "About PYNIX GUI", shortcut("d", ["primary"])),
                ],
            ),
            menu(
                "View",
                [
                    menu_item("nav-controls", "Controls"),
                    menu_item("nav-data", "Data"),
                    menu_item("nav-editor", "Rich Editor"),
                    menu_item("nav-canvas", "Canvas 2D"),
                ],
            ),
        ])
    )

    state = {
        "search": "",
        "name": "PYNIX Developer",
        "notes": "Commercial defaults, semantic API, native backend.",
        "checked": True,
        "appearance": 0,
        "scale": 72.0,
        "tree_selected": "main",
        "table_selected": "editor",
        "source": SOURCE,
        "selection_start": 0,
        "selection_end": 0,
    }
    page = "overview"

    window.render(build(page, state))

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "ACTIVATE" and event.target in DISCOVERY_ROUTES:
            page = DISCOVERY_ROUTES[event.target]
        elif event.kind == "ACTIVATE" and event.target and event.target.startswith("nav-"):
            page = event.target[4:]
        elif event.kind == "ACTIVATE" and event.target == "show-dashboard":
            page = "dashboard"
        elif event.kind == "ACTIVATE" and event.target == "open-dialog":
            window.present_dialog(
                dialog(
                    "about-gallery",
                    "PYNIX GUI",
                    column([
                        text("Commercial desktop UI with a compact semantic API.", "title"),
                        text(
                            "The Product Gallery is built from the same public components available to applications.",
                            "body",
                        ),
                        alert(
                            "Native where it matters",
                            "AppKit and Qt stay behind the PYNIX GUI boundary.",
                            "info",
                        ),
                    ], 12),
                    [
                        dialog_action(
                            "dialog-ok",
                            "Continue",
                            role="primary",
                            default=True,
                        )
                    ],
                )
            )
            continue
        elif event.kind == "CHANGE" and event.target in {
            "gallery-search", "profile-search", "settings-search", "files-search",
        }:
            state["search"] = event.text
        elif event.kind == "CHANGE" and event.target in {
            "display-name", "profile-name", "settings-name",
        }:
            state["name"] = event.text
        elif event.kind == "CHANGE" and event.target == "notes":
            state["notes"] = event.text
        elif event.kind == "CHANGE" and event.target in {"telemetry", "settings-telemetry"}:
            state["checked"] = event.checked
        elif event.kind == "CHANGE" and event.target == "scale":
            state["scale"] = event.number
        elif event.kind == "SELECTION" and event.target in {
            "appearance", "profile-theme", "settings-theme",
        }:
            state["appearance"] = event.index
        elif event.kind == "SELECTION" and event.target in {
            "gallery-tree", "ide-tree", "files-tree",
        }:
            state["tree_selected"] = event.item_id
        elif event.kind == "SELECTION" and event.target == "gallery-table":
            state["table_selected"] = event.item_id
        elif event.kind == "CHANGE" and event.target in {"gallery-editor", "ide-editor"}:
            state["source"] = event.text
            state["selection_start"] = min(state["selection_start"], len(event.text))
            state["selection_end"] = min(state["selection_end"], len(event.text))
        elif event.kind == "EDITOR_SELECTION" and event.target in {"gallery-editor", "ide-editor"}:
            state["selection_start"] = event.selection_start
            state["selection_end"] = event.selection_end
            continue
        elif event.kind == "EXPANSION":
            continue
        elif event.kind == "ACTIVATE" and event.target in {
            "canvas-card",
            "canvas-circle",
            "canvas-status",
        }:
            print("canvas activation:", event.target)
            continue
        elif event.kind == "ACTIVATE" and event.target == "dialog-ok":
            continue

        window.render(build(page, state))

    window.close()
    print("PYNIX GUI Product Gallery: PASS")


if __name__ == "__main__":
    main()
