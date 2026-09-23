"""The agent's tools for starting and advancing a project: the harness around the model.

A new address is started by asking Claude Code for one (the `new-address` skill in
.claude/skills/). What the agent does is then CALLED, not remembered:

    arkitect/harness/intake.py     the questions a drawing cannot start without, as a schema;
                          validates projects/<slug>/intake.json and prints the zoning fit
    arkitect/harness/scaffold.py   writes projects/<slug>/ from its intake: a build that draws, its
                          guard rails, its trace.md5 and its feature list, all passing
    arkitect/harness/progress.py   the feature list, projects/<slug>/progress.json: what is drawn,
                          what is checked, what comes next -- and a claim of "passes" the
                          build cannot prove is a gate failure, not a note
    arkitect/harness/catalog.py    the sheets and model checks a set is made of, and which shared
                          check guards each

Layering: harness imports arkitect/codes/ and arkitect/lib/; arkitect/lib/ and arkitect/codes/ never import harness. A
project's build imports arkitect/lib/ and arkitect/codes/, never harness, so a set builds without it.
"""
