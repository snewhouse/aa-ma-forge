"""TaskDetailScreen — drill-in view for a single Task.

Created in aa-ma-tui-tracker M3 Step 3.5 (stub) / 3.6 (compose) (2026-05-18).

Step 3.5 introduced this as a minimal stub so DashboardScreen's Enter
binding has something to push. Step 3.6 enriches `compose` with the
milestone Tree + Result Log preview + provenance tail. Step 3.7 wires
arrow-nav step selection.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Static, Tree

from aa_ma.tui.model import Step as _ModelStep
from aa_ma.tui.model import Task


class TaskDetailScreen(Screen):
    """Single-task drill-in screen pushed by DashboardScreen.action_drill_in.

    Layout:
        [detail-header]          bold task name + aggregate status
        [Horizontal body]
            [milestone-tree]     Tree of milestones → steps (each leaf carries Step)
            [result-log-preview] Static showing selected step's result_log
        [prov-tail]              joined provenance tail (last N lines — see parser._provenance_tail default)
    """

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, task: Task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.detail_task = task
        # `selected_step` set by Tree.NodeHighlighted handler in Step 3.7.
        self.selected_step: _ModelStep | None = None

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold]{self.detail_task.name}[/bold] "
            f"[{self.detail_task.aggregate_status.value}]",
            id="detail-header",
        )
        yield Horizontal(self._build_tree(), self._build_preview())
        yield self._build_prov_tail()

    # -------------------------------------------------------------------------
    # Helpers (extracted to keep compose readable and to give Step 3.7 hooks)
    # -------------------------------------------------------------------------

    def _build_tree(self) -> Tree:
        tree: Tree = Tree(self.detail_task.name, id="milestone-tree")
        for ms in self.detail_task.milestones:
            ms_node = tree.root.add(
                f"M{ms.number}: {ms.title} [{ms.status.value}]"
            )
            for step in ms.steps:
                ms_node.add_leaf(
                    f"{step.number} {step.title} [{step.status.value}]",
                    data=step,
                )
        return tree

    def _build_preview(self) -> Static:
        return Static("[dim](select a step)[/dim]", id="result-log-preview")

    def _build_prov_tail(self) -> Static:
        body = (
            "\n".join(self.detail_task.provenance_tail)
            if self.detail_task.provenance_tail
            else "[dim](no provenance entries)[/dim]"
        )
        return Static(body, id="prov-tail")

    # -------------------------------------------------------------------------
    # Step 3.7 — arrow nav selects step
    # -------------------------------------------------------------------------

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update `selected_step` + preview pane when a Tree node is highlighted.

        Milestone-level nodes carry no `data` (they show only label + status).
        Step leaves carry the Step instance via `data=step` set in _build_tree.
        Non-Step nodes are ignored.
        """
        data = event.node.data
        if not isinstance(data, _ModelStep):
            return
        self.selected_step = data
        preview = self.query_one("#result-log-preview", Static)
        preview.update(data.result_log or "[dim](no result log yet)[/dim]")
