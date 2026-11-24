"""Console-script entry point for the TiFo Streamlit GUI.

Streamlit apps cannot run by calling a plain function — they need the
``streamlit run`` server runtime. This launcher is the ``tifo-gui`` entry point:
it locates the app module and hands control to Streamlit's CLI, while giving a
friendly message if the optional GUI dependencies are not installed.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def _config_flags() -> list[str]:
    """Build ``--section.key value`` flags from the packaged config.

    Streamlit only auto-discovers ``.streamlit/config.toml`` relative to the
    current working directory (or ``~/.streamlit/``). Neither is reliable for an
    installed console script: after ``uv tool install`` the user runs
    ``tifo-gui`` from arbitrary directories, so the repo-root config — and its
    theme — is never found, and the GUI falls back to Streamlit's defaults.

    To stay CWD-independent we ship ``streamlit_config.toml`` inside the package
    and translate every option into a command-line flag. CLI flags are the
    highest-precedence config source in Streamlit, so this wins regardless of
    where the command runs or what other config files exist.
    """
    config_path = Path(__file__).resolve().parent / "streamlit_config.toml"
    if not config_path.is_file():
        return []

    with config_path.open("rb") as fh:
        config = tomllib.load(fh)

    flags: list[str] = []
    for section, options in config.items():
        if not isinstance(options, dict):
            continue
        for key, value in options.items():
            # Streamlit CLI flags use the same camelCase keys as the TOML file,
            # prefixed by the section: e.g. [theme] primaryColor -> --theme.primaryColor
            if isinstance(value, bool):
                value = "true" if value else "false"
            flags.extend([f"--{section}.{key}", str(value)])
    return flags


def main() -> None:
    try:
        from streamlit.web import cli as stcli
    except ModuleNotFoundError:
        raise SystemExit(
            "TiFo GUI dependencies are not installed.\n\n"
            "Install them with one of:\n"
            "  uv sync --group gui\n"
            "  uv tool install 'file-renamer[gui]'\n\n"
            "Then launch the GUI again with:  tifo-gui"
        )

    # First-run setup before handing off to Streamlit. The embedding model must
    # be cached up front because the app runs offline; do it here while a
    # terminal is still attached for the download spinner, not inside the
    # Streamlit subprocess where that output would be lost.
    from tifo.setup import ensure_embedder, setup_complete

    if not setup_complete():
        if not ensure_embedder():
            raise SystemExit(
                "TiFo setup is required before the GUI can run. "
                "Run `tifo-setup` once while online, then try again."
            )

    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    # Streamlit reads its target from argv, same as `streamlit run <app>`.
    #
    # Theme and server options come from the packaged ``streamlit_config.toml``,
    # translated into CLI flags by ``_config_flags()`` so they survive a global
    # install regardless of the working directory. That config also sets
    # ``server.fileWatcherType = "none"``, which matters here: Streamlit's
    # auto-reload watcher introspects every imported module to decide what to
    # watch. When it reaches ``transformers`` (pulled in by
    # sentence-transformers), that package lazily imports hundreds of vision
    # ``image_processing_*`` modules, each of which does ``import torchvision`` —
    # which TiFo intentionally does NOT install (text/CPU only). The watcher
    # catches each failure but spews a wall of harmless
    # ``ModuleNotFoundError: torchvision`` tracebacks that bury the real "app is
    # running" message. Disabling the watcher removes the noise entirely (at the
    # cost of auto-reload-on-save, which a launched app doesn't need — use
    # ``streamlit run`` directly while editing if you want reload).
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        *_config_flags(),
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
