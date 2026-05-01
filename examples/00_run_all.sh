#!/bin/bash
# -*- coding: utf-8 -*-
# File: ./examples/00_run_all.sh
# Run all scitex-audio examples in sequence.

set -e

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PATH="$THIS_DIR/$(basename "$0").log"
echo >"$LOG_PATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "$1" | tee -a "$LOG_PATH"; }

main() {
    cd "$THIS_DIR"
    echo >"$LOG_PATH"

    log "========================================"
    log "SciTeX Audio Examples Runner"
    log "========================================"
    log ""

    # Skip patterns (interactive/special)
    local SKIP_PATTERNS="quickstart"

    # Delete existing out directories
    log "Cleaning *_out directories..."
    rm -rf "$THIS_DIR"/*_out
    log "Done."
    log ""

    # Find all numbered .py files
    local -a SCRIPTS
    mapfile -t SCRIPTS < <(find . -maxdepth 1 -name '[0-9][0-9]*.py' | sort)
    local TOTAL=${#SCRIPTS[@]}
    local COUNT=0
    local PASSED=0
    local FAILED=0

    for script in "${SCRIPTS[@]}"; do
        local name
        name=$(basename "$script")

        # Skip interactive examples
        if echo "$name" | grep -qiE "$SKIP_PATTERNS"; then
            log "${YELLOW}[SKIP]${NC} $name (interactive/special)"
            continue
        fi

        COUNT=$((COUNT + 1))
        log ""
        log "[$COUNT/$TOTAL] Running $name..."

        if python "$name" >>"$LOG_PATH" 2>&1; then
            log "${GREEN}[PASS]${NC} $name"
            PASSED=$((PASSED + 1))
        else
            log "${RED}[FAIL]${NC} $name (see $LOG_PATH)"
            FAILED=$((FAILED + 1))
        fi
    done

    log ""
    log "========================================"
    log "Results: $PASSED passed, $FAILED failed, $((TOTAL - COUNT)) skipped"
    log "========================================"
    log ""
    log "Output directories:"
    find . -maxdepth 1 -type d -name '*_out' | sort | tee -a "$LOG_PATH" || log "(none)"
    log ""
    log "Log: $LOG_PATH"
}

main "$@"

# EOF
