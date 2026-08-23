"""Registry of available serving engines, keyed by the `gpu-node serve <engine>` name.

Each engine module owns its own CLI surface: `HELP` (shown in `serve --help`'s
subcommand list and as that engine's own `--help` description), `add_arguments(parser)`
(registers its engine-specific flags), and `serve(entry, **kwargs)` (does the work, with
kwargs matching the dests `add_arguments` registered). Adding a new engine is dropping in
a module with that shape and one entry here -- `cli.py` never needs to change.
"""

from backends.gpu_node.engines import llama_cpp

ENGINES = {
    "llama-cpp": llama_cpp,
}
