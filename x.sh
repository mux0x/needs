#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# CONFIG – tweak by exporting the variable before running the script ##########
###############################################################################
ALL_TARGETS="${ALL_TARGETS:-targets.txt}"            # master target list
OUT_DIR="${OUT_DIR:-bench_out}"                      # results folder
SUMMARY_CSV="$OUT_DIR/bench_summary.csv"

TEMPLATES="${TEMPLATES:-$HOME/nuclei-templates}"     # template repo path
# NUCLEI_IMAGE="${NUCLEI_IMAGE:-projectdiscovery/nuclei:latest}"

# ── fixed thread counts per requirements ─────────────────────────────────────
THREADS_SINGLE="70"          # single scan
THREADS_PARALLEL="50"        # per‑container in the parallel phase

# ── resource & traffic caps ─────────────────────────────────────────────────-
MEM_LIMIT_SINGLE="${MEM_LIMIT_SINGLE:-6g}"      # docker --memory for the 70‑thread run
MEM_LIMIT_PARALLEL="${MEM_LIMIT_PARALLEL:-4g}"  # docker --memory for each 35‑thread run

MAX_REQ_PER_HOUR="${MAX_REQ_PER_HOUR:-3600000}"        # requests / h budget
RATE_LIMIT="$(( MAX_REQ_PER_HOUR / 3600 ))"             # nuclei -rate-limit value

BS_M=25

###############################################################################

mkdir -p "$OUT_DIR"
printf "scenario,hosts,elapsed_sec,cpu_avg_pct,ram_avg_kb,ram_peak_kb\n" > "$SUMMARY_CSV"

###############################################################################
# helpers #####################################################################
###############################################################################
extract () {
  local v; v=$(grep -E "$1" "$2" | awk -F': +' '{print $2}')
  [[ -z $v ]] && { echo "❌ Missing “$1” in $2" >&2; exit 1; }
  printf '%s\n' "$v"
}

hms_to_sec () {
  local raw=${1%%.*} h=0 m=0 s=0
  IFS=: read -r h m s <<< "${raw//:/ }"
  echo $(( 10#${h:-0}*3600 + 10#${m:-0}*60 + 10#${s:-0} ))
}

strip_pct () { tr -d '%' <<< "$1"; }

NUCLEI_IMAGE="nuclei-with-time"

nuclei_run () {
  local list="$1" stats="$2" out="$3" thr="$4" mem="$5" bs="$6"

  # --- make paths absolute and guarantee that the output file exists ----
  list=$(realpath "$list")
  mkdir -p "$(dirname "$out")"   # parent dir definitely exists
  : > "$out"                     # create/truncate the file
  out=$(realpath "$out")
  # ----------------------------------------------------------------------

  /usr/bin/docker run --rm --network host \
        --memory "$mem" --memory-swap "$mem" --cpus=2 \
        -v "$list":/data/targets.txt:ro \
        -v "$out":/data/out.txt \
        -v "$(realpath "$TEMPLATES")":/templates:ro \
        "$NUCLEI_IMAGE" \
          -l /data/targets.txt \
          -templates /templates \
          -o /data/out.txt -ss host-spray -bs $bs \
          -c "$thr" -rate-limit "$RATE_LIMIT" -ep \
          2> "$stats"
}

###############################################################################
# MAIN ––– run PARALLEL first, then SINGLE ####################################
###############################################################################

total_hosts=$(wc -l < "$ALL_TARGETS")
(( total_hosts < 2 )) && { echo "Need at least two hosts." >&2; exit 1; }

###############################################################################
# 1 — split file & two parallel scans (35 threads each, 4 GiB cap) –– FIRST ###
###############################################################################
half=$(( total_hosts / 2 ))
list1="$OUT_DIR/tmp_half1.txt"; head  -n  "$half"           "$ALL_TARGETS" > "$list1"
list2="$OUT_DIR/tmp_half2.txt"; tail  -n +"$((half+1))"     "$ALL_TARGETS" > "$list2"

stats1="$OUT_DIR/stats_p1.txt"; stats2="$OUT_DIR/stats_p2.txt"
out1="$OUT_DIR/results_p1.txt"; out2="$OUT_DIR/results_p2.txt"
proj1=$(mktemp -d -t nuclei1.XXXX); proj2=$(mktemp -d -t nuclei2.XXXX)

echo -e "\n▶️  [1/2] Two Docker scans in parallel ($half + $(( total_hosts - half )) hosts)"

nuclei_run "$list1" "$stats1" "$out1" \
           "$THREADS_PARALLEL" "$MEM_LIMIT_PARALLEL" "$BS_M" & pid1=$!

nuclei_run "$list2" "$stats2" "$out2" \
           "$THREADS_PARALLEL" "$MEM_LIMIT_PARALLEL" "$BS_M" & pid2=$!

wait $pid1 $pid2

e1=$(hms_to_sec "$(extract 'Elapsed (wall clock) time' "$stats1")")
e2=$(hms_to_sec "$(extract 'Elapsed (wall clock) time' "$stats2")")
elapsed_parallel=$(( e1 > e2 ? e1 : e2 ))

c1=$(strip_pct "$(extract 'Percent of CPU this job got' "$stats1")")
c2=$(strip_pct "$(extract 'Percent of CPU this job got' "$stats2")")
cpu_parallel=$(awk "BEGIN {print ($c1 + $c2) / 2}")

r1=$(extract 'Average resident set size' "$stats1")
r2=$(extract 'Average resident set size' "$stats2")
ramavg_parallel=$(awk "BEGIN {print ($r1 + $r2) / 2}")

rmax1=$(extract 'Maximum resident set size' "$stats1")
rmax2=$(extract 'Maximum resident set size' "$stats2")
rammax_parallel=$(( rmax1 > rmax2 ? rmax1 : rmax2 ))

printf "parallel,%s,%s,%s,%s,%s\n" \
       "$total_hosts" "$elapsed_parallel" "$cpu_parallel" \
       "$ramavg_parallel" "$rammax_parallel" >> "$SUMMARY_CSV"

###############################################################################
# 2 — full‑file single‑container scan (70 threads, 6 GiB cap) –– SECOND #######
###############################################################################

echo -e "\n▶️  [2/2] Single‑container scan for $total_hosts hosts"
list_all="$OUT_DIR/tmp_all.txt"; cp "$ALL_TARGETS" "$list_all"
stats_single="$OUT_DIR/stats_single.txt"
proj_single=$(mktemp -d -t nucleiS.XXXX)
out_single="$OUT_DIR/results_single.txt"

nuclei_run "$list_all" "$stats_single" "$out_single" \
            "$THREADS_SINGLE" "$MEM_LIMIT_SINGLE"

elapsed=$(hms_to_sec "$(extract 'Elapsed (wall clock) time' "$stats_single")")
cpu_pct=$(strip_pct "$(extract 'Percent of CPU this job got' "$stats_single")")
ram_avg=$(extract 'Average resident set size' "$stats_single")
ram_peak=$(extract 'Maximum resident set size' "$stats_single")

printf "single,%s,%s,%s,%s,%s\n" \
       "$total_hosts" "$elapsed" "$cpu_pct" "$ram_avg" "$ram_peak" >> "$SUMMARY_CSV"

###############################################################################
# cleanup #####################################################################
###############################################################################
rm -rf "$proj_single" "$proj1" "$proj2"

echo -e "\n✅  Finished. Summary in $SUMMARY_CSV (directory: $OUT_DIR)"
