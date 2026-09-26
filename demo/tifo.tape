# TiFo demo tape (variant 3) — render with: vhs demo/tifo3.tape
# Mirrors demo/tifo.tape's flow/structure. Timings kept from the previous
# tifo3.tape as-is (not tuned yet).
#
# Flow (folder organization path):
#   uv run python -m src.app
#     → Select Language        (English, default/top)          -> Enter
#     → Enter folder path                                      -> type + Enter
#     → Select pipeline        (Rename + Folder Organization)  -> Down, Enter
#     → Select Folder Strategy (Organize by File Type)         -> Down, Enter
#     → Choose naming format   (Title Case, default/top)       -> Enter
#     → Confirmation (Accept All, top)                         -> Enter

# ---- Output ----
Output demo/tifo3.gif

# ---- Terminal look (matched to demo/tifo.tape) ----
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 700
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 60ms

# ---- Setup (not recorded): force a clean prompt ----
# The messy text in the GIF was the Powerlevel10k prompt TEMPLATE being dumped
# as literal text (a zsh p10k prompt fed into bash, which can't expand it).
# Override PS1 with a plain prompt and unset the broken PROMPT_COMMAND so it
# stops redrawing the garbage on every line.
Hide
Type "unset PROMPT_COMMAND; PS1='$ '"
Enter
Type "cd /home/briant_s/Documents/Code/semester_5/Venture/file_renamer"
Enter
Type "clear"
Enter
Show

# ---- Start the tool ----
Sleep 3.5s
Type "uv run python -m src.app"
Enter
# initial wait for uv + imports + banner
Sleep 4.5s

# ---- Prompt 1: Select Language (English is default/top) ----
Enter
Sleep 1s

# ---- Prompt 2: folder path (questionary.path, only_directories) ----
Type "demo/sample"
Enter
Sleep 1s

# ---- Prompt 3: Select pipeline ----
# choices: [Rename Files Only, Rename + Folder Organization]  (2 items)
# ONE Down -> "Rename + Folder Organization"
Down
Enter
Sleep 1.5s

# ---- Prompt 4: Select Folder Strategy ----
# choices: [Manually Write Folder Names, Organize by File Type, Auto Organize]
# ONE Down -> "Organize by File Type"
Down
Enter
Sleep 1s

# ---- Naming format prompt (Title Case is default/top) ----
Enter
Sleep 1.5s

# ---- Confirmation: ask_rename_option -> [Accept All, Individual Edit, Cancel]
# Accept All is top -> Enter
Enter
Sleep 5s
