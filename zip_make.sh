zip -r Archive.zip . -x "**/__pycache__/*" -x "*.pyc" ".*" -x "*/.*"

# **/__pycache__/*
# All __pycache__ folders and contents
# *.pyc
# All compiled Python files
# .*
# Dotfiles in the root dir (e.g., .gitignore)
# */.*
# Dotfiles inside folders (e.g., .DS_Store, .env, etc.)
