"""arkitect in a browser: a local web UI over the same files and the same --json tools.

    arkitect web [--port 8765] [--no-open]

The UI is a view over the workspace: every action it offers is a command the CLI already has,
run in the workspace, and what it shows is those commands' JSON (docs/interface.md). It adds
no state a drawing depends on. See docs/web-ui.md.
"""
