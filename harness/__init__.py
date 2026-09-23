"""The agent's tools for starting and advancing a project: the harness around the model.

A new address is started by asking Claude Code for one (the `new-address` skill in
.claude/skills/). What the agent does is then CALLED, not remembered:

    harness/intake.py     the questions a drawing cannot start without, as a schema;
                          validates projects/<slug>/intake.json and prints the zoning fit
    harness/scaffold.py   writes projects/<slug>/ from its intake: a build that draws, its
                          guard rails, its trace.md5 and its feature list, all passing
    harness/progress.py   the feature list, projects/<slug>/progress.json: what is drawn,
                          what is checked, what comes next -- and a claim of "passes" the
                          build cannot prove is a gate failure, not a note
    harness/catalog.py    the sheets and model checks a set is made of, and which shared
                          check guards each

Layering: harness imports codes/ and lib/; lib/ and codes/ never import harness. A
project's build imports lib/ and codes/, never harness, so a set builds without it.
"""
