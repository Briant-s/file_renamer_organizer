# TiFo GUI assets

Drop the TiFo logo image files **in this folder** (`tifo/gui/assets/`). The
Streamlit app loads them by these exact filenames, so name them accordingly:

| File                | Used for                                   | Recommended size            |
| ------------------- | ------------------------------------------ | --------------------------- |
| `logo.png`          | Main logo shown at the top of the app      | ~200–400 px wide, transparent background |
| `logo_small.png`    | Collapsed-sidebar / compact icon (optional)| square, ~64–128 px          |
| `favicon.png`       | Browser tab icon (optional)                | square, 32–64 px            |

Notes:

- **PNG with a transparent background** is recommended so the logo sits cleanly
  on the dark theme (`#0e1117`). SVG also works for `logo.png`.
- These files live **inside the package** (`tifo/gui/assets/`) on purpose: they
  are bundled into the wheel by hatch (`[tool.hatch.build.targets.wheel]
  packages = ["tifo"]`), so `tifo-gui` finds the logo even after
  `uv tool install`.
- All three are **optional**. If a file is missing the app falls back
  gracefully: no main logo is shown, and the tab icon defaults to the 📁 emoji.
  Add the files and re-run `tifo-gui` — no code changes needed.

The brand colors (matching the CLI banners) are:

- Primary green `#008700`  (rich `green4`)
- Clustering accent `#d78700`  (rich `orange3`)
- Rename accent `#00af87`  (rich `dark_cyan`)
