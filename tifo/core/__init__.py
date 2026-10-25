"""Pure-logic core shared by every TiFo frontend.

Modules in this package MUST NOT import any presentation library
(``rich``, ``questionary``, ``streamlit``). They take plain data in and
return plain data out, so the CLI and the Streamlit GUI can both drive the
same engine without duplicating logic.
"""
