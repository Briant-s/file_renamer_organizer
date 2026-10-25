"""Console-script entry point for the TiFo Streamlit GUI.

Streamlit apps cannot run by calling a plain function — they need the
``streamlit run`` server runtime. This launcher is the ``tifo-gui`` entry point:
it locates the app module and hands control to Streamlit's CLI, while giving a
friendly message if the optional GUI dependencies are not installed.
"""

from __future__ import annotations

import sys
from pathlib import Path


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

    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    # Streamlit reads its target from argv, same as `streamlit run <app>`.
    #
    # ``fileWatcherType=none`` is important here: Streamlit's auto-reload
    # watcher introspects every imported module to decide what to watch. When
    # it reaches ``transformers`` (pulled in by sentence-transformers), that
    # package lazily imports hundreds of vision ``image_processing_*`` modules,
    # each of which does ``import torchvision`` — which TiFo intentionally does
    # NOT install (text/CPU only). The watcher catches each failure but spews a
    # wall of harmless ``ModuleNotFoundError: torchvision`` tracebacks that bury
    # the real "app is running" message. Disabling the watcher removes the noise
    # entirely (at the cost of auto-reload-on-save, which a launched app doesn't
    # need — use ``streamlit run`` directly while editing if you want reload).
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.fileWatcherType=none",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
