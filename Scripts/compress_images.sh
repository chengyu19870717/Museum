#!/usr/bin/env bash
# #8: Compress museum images to max 1200px on the long edge.
# Uses macOS built-in `sips` — no extra dependencies needed.
# Usage:
#   bash Scripts/compress_images.sh            # dry-run (shows sizes)
#   bash Scripts/compress_images.sh --apply    # apply compression in-place

set -euo pipefail

MUSEUM_DATA="$(cd "$(dirname "$0")/.." && pwd)/MuseumData"
MAX_PX=1200
DRY_RUN=true

for arg in "$@"; do
  [[ "$arg" == "--apply" ]] && DRY_RUN=false
done

total_before=0
total_after=0
count=0

while IFS= read -r -d '' img; do
  size_before=$(stat -f%z "$img")
  total_before=$((total_before + size_before))

  # Skip images whose long edge is already ≤ MAX_PX (sips would upscale them)
  img_px=$(sips -g pixelWidth -g pixelHeight "$img" 2>/dev/null \
    | awk '/pixel(Width|Height)/{print $2}' | sort -rn | head -1)
  if [[ -n "$img_px" && "$img_px" -le "$MAX_PX" ]]; then
    total_after=$((total_after + size_before))
    if $DRY_RUN; then
      echo "[skip]   $(printf '%6d KB' $((size_before / 1024)))  ${img_px}px — already small  $img"
    else
      echo "[skip]   $(printf '%6d KB' $((size_before / 1024)))  ${img_px}px — already small  $img"
    fi
    count=$((count + 1))
    continue
  fi

  if $DRY_RUN; then
    echo "[dry-run] $(printf '%6d KB' $((size_before / 1024)))  $img"
  else
    sips -Z "$MAX_PX" "$img" --out "$img" > /dev/null 2>&1
    size_after=$(stat -f%z "$img")
    total_after=$((total_after + size_after))
    saved=$((size_before - size_after))
    echo "[ok] $(printf '%6d KB → %6d KB  (-%d KB)' \
      $((size_before / 1024)) $((size_after / 1024)) $((saved / 1024)))  $img"
  fi
  count=$((count + 1))
done < <(find "$MUSEUM_DATA" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -print0)

echo ""
echo "Total images: $count"
if $DRY_RUN; then
  echo "Total size:   $((total_before / 1024 / 1024)) MB"
  echo "Run with --apply to compress."
else
  echo "Before: $((total_before / 1024 / 1024)) MB"
  echo "After:  $((total_after / 1024 / 1024)) MB"
  echo "Saved:  $(( (total_before - total_after) / 1024 / 1024 )) MB"
fi
