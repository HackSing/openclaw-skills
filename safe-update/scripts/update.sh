#!/bin/bash
# Safe Update Script
# Update OpenClaw using official or developer mode with backup and rollback metadata.

set -euo pipefail

PROJECT_DIR="${OPENCLAW_PROJECT_DIR:-$HOME/projects/openclaw}"
BRANCH="${OPENCLAW_BRANCH:-main}"
DRY_RUN="${DRY_RUN:-false}"
UPDATE_MODE="${OPENCLAW_UPDATE_MODE:-merge}"
UPSTREAM_REF="${OPENCLAW_UPSTREAM_REF:-upstream/main}"
INSTALL_MODE="${OPENCLAW_INSTALL_MODE:-auto}"
BACKUP_DIR_ROOT="${OPENCLAW_BACKUP_DIR:-$HOME/.openclaw/backups/safe-update}"
PACKAGE_FILE=""
SELECTED_INSTALL_MODE=""
BACKUP_DIR=""
ROLLBACK_SCRIPT=""
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
GLOBAL_NPM_ROOT=""
GLOBAL_INSTALL_DIR=""
PREVIOUS_GLOBAL_VERSION=""
PREVIOUS_GATEWAY_COMMAND=""
PREVIOUS_REALPATH=""
PREVIOUS_HEAD=""
PREVIOUS_BRANCH=""
PREVIOUS_STATUS_SUMMARY=""
PREVIOUS_PACKAGE_VERSION=""
PREVIOUS_PACKAGE_NAME=""
HAS_UPSTREAM_REMOTE="false"
REPO_LOOKS_LIKE_OPENCLAW="false"
REPO_REMOTE_MATCHED="false"
AUTO_DETECTION_REASON=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dir PATH              OpenClaw project directory default: $PROJECT_DIR
  --branch NAME           Git branch to update default: $BRANCH
  --mode MODE             Git update mode: merge or rebase default: $UPDATE_MODE
  --upstream-ref REF      Upstream ref to merge or rebase onto default: $UPSTREAM_REF
  --install-mode MODE     auto, official, or developer default: $INSTALL_MODE
  --backup-dir PATH       Backup root directory default: $BACKUP_DIR_ROOT
  --dry-run               Show what would be done without executing
  --help                  Show this help message

Environment Variables:
  OPENCLAW_PROJECT_DIR    Project directory default: ~/projects/openclaw
  OPENCLAW_BRANCH         Git branch default: main
  OPENCLAW_UPDATE_MODE    merge or rebase default: merge
  OPENCLAW_UPSTREAM_REF   upstream ref default: upstream/main
  OPENCLAW_INSTALL_MODE   auto, official, or developer default: auto
  OPENCLAW_BACKUP_DIR     Backup root directory
  DRY_RUN                 Set to true for dry-run mode
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --mode)
            UPDATE_MODE="$2"
            shift 2
            ;;
        --upstream-ref)
            UPSTREAM_REF="$2"
            shift 2
            ;;
        --install-mode)
            INSTALL_MODE="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR_ROOT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

run_cmd() {
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute: $*"
    else
        log_info "Executing: $*"
        "$@"
    fi
}

run_shell() {
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute shell: $*"
    else
        log_info "Executing shell: $*"
        bash -lc "$*"
    fi
}

write_file() {
    local path="$1"
    shift
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would write file: $path"
        return
    fi
    mkdir -p "$(dirname "$path")"
    cat > "$path"
}

append_file() {
    local path="$1"
    shift
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would append file: $path"
        return
    fi
    mkdir -p "$(dirname "$path")"
    cat >> "$path"
}

validate_branch() {
    local branch="$1"
    if [[ ! "$branch" =~ ^[a-zA-Z0-9][a-zA-Z0-9_./-]*$ ]]; then
        log_error "Invalid branch name: $branch"
        exit 1
    fi
}

validate_ref() {
    local ref="$1"
    if [[ ! "$ref" =~ ^[a-zA-Z0-9][a-zA-Z0-9_./-]*$ ]]; then
        log_error "Invalid ref: $ref"
        exit 1
    fi
}

validate_mode() {
    case "$1" in
        merge|rebase) ;;
        *)
            log_error "Invalid update mode: $1"
            log_error "Expected merge or rebase"
            exit 1
            ;;
    esac
}

validate_install_mode() {
    case "$1" in
        auto|official|developer) ;;
        *)
            log_error "Invalid install mode: $1"
            log_error "Expected auto, official, or developer"
            exit 1
            ;;
    esac
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing=()
    for cmd in git npm node openclaw; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required binaries: ${missing[*]}"
        exit 1
    fi

    log_info "All dependencies found: git, npm, node, openclaw"
}

check_project() {
    log_info "Checking project directory: $PROJECT_DIR"

    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory does not exist: $PROJECT_DIR"
        exit 1
    fi

    if [ ! -d "$PROJECT_DIR/.git" ]; then
        log_error "Not a git repository: $PROJECT_DIR"
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/package.json" ]; then
        log_error "package.json not found: $PROJECT_DIR"
        exit 1
    fi

    log_info "Project directory valid"
}

capture_environment() {
    cd "$PROJECT_DIR"
    GLOBAL_NPM_ROOT="$(npm root -g)"
    GLOBAL_INSTALL_DIR="$GLOBAL_NPM_ROOT/openclaw"
    PREVIOUS_GLOBAL_VERSION="$(openclaw --version 2>/dev/null | head -n 1 || true)"
    PREVIOUS_GATEWAY_COMMAND="$(openclaw gateway status 2>/dev/null | sed -n 's/^Command: //p' | head -n 1 || true)"
    PREVIOUS_REALPATH="$(python3 - <<PY
import os
p = os.path.expanduser('$GLOBAL_INSTALL_DIR')
print(os.path.realpath(p) if os.path.exists(p) else '')
PY
)"
    PREVIOUS_HEAD="$(git rev-parse HEAD)"
    PREVIOUS_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    PREVIOUS_STATUS_SUMMARY="$(git status --short | sed -n '1,30p' || true)"
    PREVIOUS_PACKAGE_NAME="$(node -p "require('$PROJECT_DIR/package.json').name" 2>/dev/null || true)"
    PREVIOUS_PACKAGE_VERSION="$(node -p "require('$PROJECT_DIR/package.json').version" 2>/dev/null || true)"
    if [ "$PREVIOUS_PACKAGE_NAME" = "openclaw" ]; then
        REPO_LOOKS_LIKE_OPENCLAW="true"
    else
        REPO_LOOKS_LIKE_OPENCLAW="false"
    fi

    local remote_urls=""
    remote_urls="$(git remote -v 2>/dev/null || true)"
    if grep -Eq 'github\.com[:/](openclaw/openclaw|HackSing/openclaw)(\.git)?' <<<"$remote_urls"; then
        REPO_REMOTE_MATCHED="true"
    else
        REPO_REMOTE_MATCHED="false"
    fi

    if git remote get-url upstream >/dev/null 2>&1; then
        HAS_UPSTREAM_REMOTE="true"
    else
        HAS_UPSTREAM_REMOTE="false"
    fi
}

check_git_status() {
    log_info "Checking git status..."
    cd "$PROJECT_DIR"

    if [ -n "$(git status --porcelain)" ]; then
        log_warn "You have uncommitted changes"
        log_warn "Please commit or stash them before updating"
        if [ "$DRY_RUN" != "true" ]; then
            read -r -p "Continue anyway? y/N " reply
            if [[ ! "$reply" =~ ^[Yy]$ ]]; then
                log_info "Aborted"
                exit 0
            fi
        fi
    fi
}

select_install_mode() {
    cd "$PROJECT_DIR"

    if [ "$INSTALL_MODE" != "auto" ]; then
        SELECTED_INSTALL_MODE="$INSTALL_MODE"
        log_info "Install mode forced by user: $SELECTED_INSTALL_MODE"
        return
    fi

    local branch current_branch ahead_count behind_count has_dirty has_unpushed has_upstream_updates install_is_symlink
    current_branch="$(git rev-parse --abbrev-ref HEAD)"
    branch="$BRANCH"
    if [ -z "$branch" ]; then
        branch="$current_branch"
    fi

    has_dirty="false"
    has_unpushed="false"
    has_upstream_updates="false"
    install_is_symlink="false"
    AUTO_DETECTION_REASON="default-to-official"

    if [ -n "$(git status --porcelain)" ]; then
        has_dirty="true"
    fi

    if git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
        ahead_count="$(git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo 0)"
        behind_count="$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo 0)"
        if [ "${ahead_count:-0}" -gt 0 ]; then
            has_unpushed="true"
        fi
        if [ "${behind_count:-0}" -gt 0 ]; then
            has_upstream_updates="true"
        fi
    fi

    if [ -L "$GLOBAL_INSTALL_DIR" ]; then
        install_is_symlink="true"
    fi

    if [ "$REPO_LOOKS_LIKE_OPENCLAW" = "true" ] && [ "$REPO_REMOTE_MATCHED" = "true" ]; then
        SELECTED_INSTALL_MODE="developer"
        AUTO_DETECTION_REASON="source-repo-maintainer"
    elif [ "$current_branch" != "main" ] || [ "$has_dirty" = "true" ] || [ "$has_unpushed" = "true" ] || [ "$install_is_symlink" = "true" ]; then
        SELECTED_INSTALL_MODE="developer"
        AUTO_DETECTION_REASON="customized-or-linked-runtime"
    else
        SELECTED_INSTALL_MODE="official"
        AUTO_DETECTION_REASON="package-runtime"
    fi

    log_info "Auto-detected install mode: $SELECTED_INSTALL_MODE"
    log_info "Detection reason: $AUTO_DETECTION_REASON"
    log_info "Detection evidence: branch=$current_branch dirty=$has_dirty unpushed=$has_unpushed upstreamUpdates=$has_upstream_updates symlinkInstall=$install_is_symlink repoOpenClaw=$REPO_LOOKS_LIKE_OPENCLAW remoteMatched=$REPO_REMOTE_MATCHED"
}

prepare_backup_dir() {
    BACKUP_DIR="$BACKUP_DIR_ROOT/$TIMESTAMP"
    ROLLBACK_SCRIPT="$BACKUP_DIR/rollback.sh"

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would create backup directory: $BACKUP_DIR"
        return
    fi

    mkdir -p "$BACKUP_DIR"
}

backup_runtime_snapshot() {
    local runtime_archive="$BACKUP_DIR/installed-runtime-before-update.tar.gz"

    if [ ! -d "$GLOBAL_INSTALL_DIR" ]; then
        return
    fi

    if [ -L "$GLOBAL_INSTALL_DIR" ]; then
        log_warn "Skipping runtime snapshot because global install dir is a symlink: $GLOBAL_INSTALL_DIR"
        return
    fi

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would create runtime snapshot: $runtime_archive"
        return
    fi

    log_info "Creating runtime snapshot from $GLOBAL_INSTALL_DIR"
    tar -C "$GLOBAL_NPM_ROOT" -czf "$runtime_archive" openclaw
}

backup_repo_state() {
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would capture git diff and bundle into $BACKUP_DIR"
        return
    fi

    git -C "$PROJECT_DIR" diff > "$BACKUP_DIR/git-working-tree.diff" 2>/dev/null || true
    git -C "$PROJECT_DIR" diff --cached > "$BACKUP_DIR/git-staged.diff" 2>/dev/null || true
    git -C "$PROJECT_DIR" bundle create "$BACKUP_DIR/repo.bundle" --all >/dev/null 2>&1 || true
}

backup_state() {
    log_info "Backing up update metadata and critical files..."
    prepare_backup_dir

    local config_path="$HOME/.openclaw/openclaw.json"
    local main_auth_path="$HOME/.openclaw/agents/main/agent/auth-profiles.json"
    local coder_auth_path="$HOME/.openclaw/agents/coder/agent/auth-profiles.json"

    if [ -f "$config_path" ]; then
        run_cmd cp "$config_path" "$BACKUP_DIR/openclaw.json"
    fi

    if [ -f "$main_auth_path" ]; then
        run_cmd cp "$main_auth_path" "$BACKUP_DIR/auth-profiles-main.json"
    fi

    if [ -f "$coder_auth_path" ]; then
        run_cmd cp "$coder_auth_path" "$BACKUP_DIR/auth-profiles-coder.json"
    fi

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would capture status files into $BACKUP_DIR"
    else
        openclaw status > "$BACKUP_DIR/openclaw-status.txt" 2>&1 || true
        openclaw gateway status > "$BACKUP_DIR/gateway-status.txt" 2>&1 || true
        git -C "$PROJECT_DIR" status > "$BACKUP_DIR/git-status.txt" 2>&1 || true
        git -C "$PROJECT_DIR" log --oneline -n 30 > "$BACKUP_DIR/git-log.txt" 2>&1 || true
        npm ls -g openclaw --depth=0 > "$BACKUP_DIR/npm-global-openclaw.txt" 2>&1 || true
        if [ -f "$GLOBAL_INSTALL_DIR/package.json" ]; then
            cp "$GLOBAL_INSTALL_DIR/package.json" "$BACKUP_DIR/installed-package.json"
        fi
    fi

    backup_repo_state

    if [ "$SELECTED_INSTALL_MODE" = "developer" ]; then
        backup_runtime_snapshot
    fi

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would write file: $BACKUP_DIR/metadata.json"
    else
        TIMESTAMP_JSON="$TIMESTAMP" \
        PROJECT_DIR_JSON="$PROJECT_DIR" \
        SELECTED_INSTALL_MODE_JSON="$SELECTED_INSTALL_MODE" \
        INSTALL_MODE_JSON="$INSTALL_MODE" \
        UPDATE_MODE_JSON="$UPDATE_MODE" \
        UPSTREAM_REF_JSON="$UPSTREAM_REF" \
        BRANCH_JSON="$BRANCH" \
        PREVIOUS_HEAD_JSON="$PREVIOUS_HEAD" \
        PREVIOUS_BRANCH_JSON="$PREVIOUS_BRANCH" \
        PREVIOUS_GLOBAL_VERSION_JSON="$PREVIOUS_GLOBAL_VERSION" \
        PREVIOUS_PACKAGE_NAME_JSON="$PREVIOUS_PACKAGE_NAME" \
        PREVIOUS_PACKAGE_VERSION_JSON="$PREVIOUS_PACKAGE_VERSION" \
        PREVIOUS_GATEWAY_COMMAND_JSON="$PREVIOUS_GATEWAY_COMMAND" \
        PREVIOUS_REALPATH_JSON="$PREVIOUS_REALPATH" \
        GLOBAL_INSTALL_DIR_JSON="$GLOBAL_INSTALL_DIR" \
        HAS_UPSTREAM_REMOTE_JSON="$HAS_UPSTREAM_REMOTE" \
        REPO_LOOKS_LIKE_OPENCLAW_JSON="$REPO_LOOKS_LIKE_OPENCLAW" \
        REPO_REMOTE_MATCHED_JSON="$REPO_REMOTE_MATCHED" \
        AUTO_DETECTION_REASON_JSON="$AUTO_DETECTION_REASON" \
        python3 - <<'PY' > "$BACKUP_DIR/metadata.json"
import json
import os

print(json.dumps({
  "timestamp": os.environ.get("TIMESTAMP_JSON", ""),
  "projectDir": os.environ.get("PROJECT_DIR_JSON", ""),
  "selectedInstallMode": os.environ.get("SELECTED_INSTALL_MODE_JSON", ""),
  "requestedInstallMode": os.environ.get("INSTALL_MODE_JSON", ""),
  "gitUpdateMode": os.environ.get("UPDATE_MODE_JSON", ""),
  "upstreamRef": os.environ.get("UPSTREAM_REF_JSON", ""),
  "branch": os.environ.get("BRANCH_JSON", ""),
  "previousHead": os.environ.get("PREVIOUS_HEAD_JSON", ""),
  "previousBranch": os.environ.get("PREVIOUS_BRANCH_JSON", ""),
  "previousGlobalVersion": os.environ.get("PREVIOUS_GLOBAL_VERSION_JSON", ""),
  "previousPackageName": os.environ.get("PREVIOUS_PACKAGE_NAME_JSON", ""),
  "previousPackageVersion": os.environ.get("PREVIOUS_PACKAGE_VERSION_JSON", ""),
  "previousGatewayCommand": os.environ.get("PREVIOUS_GATEWAY_COMMAND_JSON", ""),
  "previousInstallRealpath": os.environ.get("PREVIOUS_REALPATH_JSON", ""),
  "globalInstallDir": os.environ.get("GLOBAL_INSTALL_DIR_JSON", ""),
  "hasUpstreamRemote": os.environ.get("HAS_UPSTREAM_REMOTE_JSON", ""),
  "repoLooksLikeOpenClaw": os.environ.get("REPO_LOOKS_LIKE_OPENCLAW_JSON", ""),
  "repoRemoteMatched": os.environ.get("REPO_REMOTE_MATCHED_JSON", ""),
  "autoDetectionReason": os.environ.get("AUTO_DETECTION_REASON_JSON", ""),
}, indent=2, ensure_ascii=False))
PY
    fi

    create_rollback_script
    log_info "Backup saved to: $BACKUP_DIR"
}

create_rollback_script() {
    write_file "$ROLLBACK_SCRIPT" <<EOF
#!/bin/bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR}"
PREVIOUS_HEAD="${PREVIOUS_HEAD}"
PREVIOUS_BRANCH="${PREVIOUS_BRANCH}"
PREVIOUS_GLOBAL_VERSION="${PREVIOUS_GLOBAL_VERSION}"
PREVIOUS_PACKAGE_NAME="${PREVIOUS_PACKAGE_NAME}"
PREVIOUS_PACKAGE_VERSION="${PREVIOUS_PACKAGE_VERSION}"
SELECTED_INSTALL_MODE="${SELECTED_INSTALL_MODE}"
BACKUP_DIR="${BACKUP_DIR}"
GLOBAL_NPM_ROOT="${GLOBAL_NPM_ROOT}"
GLOBAL_INSTALL_DIR="${GLOBAL_INSTALL_DIR}"

echo "Rollback helper for Safe Update"
echo "Project Dir: \\$PROJECT_DIR"
echo "Previous Branch: \\$PREVIOUS_BRANCH"
echo "Previous Head: \\$PREVIOUS_HEAD"
echo "Previous Global Version: \\$PREVIOUS_GLOBAL_VERSION"
echo "Previous Package: \\$PREVIOUS_PACKAGE_NAME@\\$PREVIOUS_PACKAGE_VERSION"
echo "Selected Install Mode: \\$SELECTED_INSTALL_MODE"
echo ""

echo "Suggested rollback steps:"
echo "1. cd \\$PROJECT_DIR"
echo "2. git checkout \\$PREVIOUS_BRANCH"
echo "3. git reset --hard \\$PREVIOUS_HEAD"
if [ -f "\\$BACKUP_DIR/git-working-tree.diff" ]; then
  echo "4. Optional: git apply \\$BACKUP_DIR/git-working-tree.diff"
fi
if [ "${SELECTED_INSTALL_MODE}" = "official" ]; then
  echo "5. npm install -g openclaw@<known-good-version>"
else
  echo "5. If runtime snapshot exists, restore it to \\$GLOBAL_NPM_ROOT:"
  echo "   tar -C \\$GLOBAL_NPM_ROOT -xzf \\$BACKUP_DIR/installed-runtime-before-update.tar.gz"
  echo "   or rebuild from the repo state above"
fi
echo "6. openclaw daemon install --force"
echo "7. openclaw gateway restart"
echo ""
echo "Backed up files are in: \\$BACKUP_DIR"
EOF
    if [ "$DRY_RUN" != "true" ]; then
        chmod +x "$ROLLBACK_SCRIPT"
    fi
}

create_package() {
    log_info "Building source tree..."
    run_cmd npm run build

    log_info "Packing source tree into a publish-style tarball..."
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute shell: cd '$PROJECT_DIR' && npm pack"
        PACKAGE_FILE="$(node -p "require('$PROJECT_DIR/package.json').name + '-' + require('$PROJECT_DIR/package.json').version + '.tgz'")"
        return
    fi

    local pack_output
    pack_output="$(cd "$PROJECT_DIR" && npm pack)"
    PACKAGE_FILE="$(printf '%s\n' "$pack_output" | tail -n 1 | tr -d '\r')"

    if [ -z "$PACKAGE_FILE" ] || [ ! -f "$PROJECT_DIR/$PACKAGE_FILE" ]; then
        log_error "Failed to resolve npm pack output tarball"
        exit 1
    fi

    log_info "Created package tarball: $PROJECT_DIR/$PACKAGE_FILE"
}

verify_install_target() {
    local install_dir
    install_dir="$(npm root -g)/openclaw"

    if [ ! -f "$install_dir/dist/index.js" ]; then
        log_error "Installed runtime entry missing: $install_dir/dist/index.js"
        exit 1
    fi

    if [ -L "$install_dir" ]; then
        log_error "Installed runtime directory is still a symlink: $install_dir"
        exit 1
    fi

    log_info "Verified installed runtime entry: $install_dir/dist/index.js"
    log_info "Verified installed runtime directory is a real directory"
}

official_update() {
    log_info "Running official update mode..."
    log_info "This mode follows the official recommended path as closely as possible."
    run_cmd openclaw update
    run_cmd openclaw doctor
}

developer_update() {
    log_info "Running developer update mode..."
    run_shell "git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/openclaw/openclaw.git"
    run_cmd git fetch upstream
    run_cmd git checkout "$BRANCH"

    if [ "$UPDATE_MODE" = "rebase" ]; then
        run_cmd git rebase "$UPSTREAM_REF"
    else
        run_cmd git merge "$UPSTREAM_REF"
    fi

    create_package

    log_info "Installing tarball into global npm runtime directory..."
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute shell: npm uninstall -g openclaw && npm install -g '$PROJECT_DIR/$PACKAGE_FILE'"
    else
        run_cmd npm uninstall -g openclaw
        run_cmd npm install -g "$PROJECT_DIR/$PACKAGE_FILE"
        verify_install_target
    fi

    log_info "Rebinding gateway service to installed runtime..."
    run_cmd openclaw daemon install --force
}

restart_gateway() {
    log_info "Restarting Gateway via OpenClaw daemon manager..."
    run_cmd openclaw gateway restart
}

verify_runtime_binding() {
    if [ "$DRY_RUN" = "true" ]; then
        return
    fi

    local gateway_status expected
    gateway_status="$(openclaw gateway status)"
    echo "$gateway_status"

    if [ "$SELECTED_INSTALL_MODE" = "developer" ]; then
        expected="$(npm root -g)/openclaw/dist/index.js"
        if ! grep -Fq "$expected" <<<"$gateway_status"; then
            log_error "Gateway is not bound to installed runtime: $expected"
            exit 1
        fi
        log_info "Gateway runtime binding verified for developer mode"
    else
        log_info "Official mode completed. Gateway status captured for verification."
    fi
}

verify_extension_dependency() {
    if [ "$DRY_RUN" = "true" ]; then
        return
    fi

    local install_dir feishu_dir
    install_dir="$(npm root -g)/openclaw"
    feishu_dir="$install_dir/extensions/feishu"

    if [ -f "$feishu_dir/package.json" ]; then
        log_info "Checking Feishu extension dependency resolution..."
        if ! node -e "require.resolve('@larksuiteoapi/node-sdk', { paths: ['$feishu_dir'] });" >/dev/null 2>&1; then
            log_warn "Feishu extension dependency missing in installed runtime"
            log_warn "Installing extension-local dependencies in $feishu_dir"
            run_shell "cd '$feishu_dir' && npm install"
        fi
    fi
}

verify_health() {
    if [ "$DRY_RUN" = "true" ]; then
        return
    fi

    log_info "Checking gateway health..."
    openclaw status | sed -n '1,80p'
}

main() {
    echo "========================================"
    echo "       Safe Update for OpenClaw"
    echo "========================================"
    echo ""
    echo "Configuration:"
    echo "  Project Dir:     $PROJECT_DIR"
    echo "  Branch:          $BRANCH"
    echo "  Update Mode:     $UPDATE_MODE"
    echo "  Upstream Ref:    $UPSTREAM_REF"
    echo "  Install Mode:    $INSTALL_MODE"
    echo "  Backup Dir Root: $BACKUP_DIR_ROOT"
    echo "  Dry Run:         $DRY_RUN"
    echo ""

    if [ "$DRY_RUN" = "true" ]; then
        log_warn "DRY-RUN MODE: No actual changes will be made"
        echo ""
    fi

    echo "========================================"
    echo "⚠️  PRE-RUN CHECKLIST"
    echo "========================================"
    echo "Before continuing, ensure you have:"
    echo "  [ ] Confirmed the update scope and target mode"
    echo "  [ ] Allowed backup creation before mutation"
    echo "  [ ] Committed or stashed local changes if needed"
    echo ""

    if [ "$DRY_RUN" != "true" ]; then
        read -r -p "Continue with update? y/N " reply
        if [[ ! "$reply" =~ ^[Yy]$ ]]; then
            log_info "Aborted"
            exit 0
        fi
    fi

    validate_branch "$BRANCH"
    validate_mode "$UPDATE_MODE"
    validate_ref "$UPSTREAM_REF"
    validate_install_mode "$INSTALL_MODE"

    check_dependencies
    check_project
    capture_environment
    select_install_mode
    check_git_status
    backup_state

    log_info "Starting update process..."
    cd "$PROJECT_DIR"

    if [ "$SELECTED_INSTALL_MODE" = "official" ]; then
        official_update
    else
        developer_update
    fi

    verify_extension_dependency
    restart_gateway
    verify_runtime_binding
    verify_health

    echo ""
    echo "========================================"
    echo "✅ Update Process Complete!"
    echo "========================================"
    echo ""
    echo "Selected install mode: $SELECTED_INSTALL_MODE"
    echo "Backup directory: $BACKUP_DIR"
    echo "Rollback helper: $ROLLBACK_SCRIPT"
}

main
