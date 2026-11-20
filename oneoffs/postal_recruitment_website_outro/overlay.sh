#!/usr/bin/env bash
set -euo pipefail
input=$1
picture=$2
output=$3
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$input" -loop 1 -framerate 30 -i "$picture" \
  -filter_complex "[1:v]scale=416:248,format=yuva420p,fade=t=in:st=27.8:d=0.45:alpha=1[card];[0:v][card]overlay=x=(W-w)/2:y='816+20*clip(1-(t-27.8)/0.45,0,1)':enable='gte(t,27.8)':shortest=1[final]" \
  -map '[final]' -map 0:a:0 -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p -c:a copy -movflags +faststart "$output"
ffmpeg -nostdin -v error -xerror -i "$output" -f null -
