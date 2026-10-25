"""Streamlit GUI frontend for TiFo.

This package contains the browser UI only. All business logic is imported from
:mod:`tifo.core`, so the GUI never reimplements rename/organize behavior and
never touches the CLI's ``rich``/``questionary`` layer.
"""
