#!/usr/bin/env bash
# Render a single PNG frame and open it immediately.
# Usage: ./preview.sh [SceneClass] [SceneFile]
#   SceneClass defaults to Intro
#   SceneFile  defaults to src/scenes/s00_intro.py

SCENE=${1:-Intro}
FILE=${2:-src/scenes/s00_intro.py}

manim -s -ql "$FILE" "$SCENE" && \
  open media/images/"$(basename "$FILE" .py)"/"${SCENE}"_ManimCE_*.png
