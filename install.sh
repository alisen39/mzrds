#!/usr/bin/env bash
# mzrds 一键安装脚本

set -euo pipefail

VERSION="${MZRDS_VERSION:-latest}"
REPO="${MZRDS_REPO:-alisen39/mzrds}"
INSTALL_DIR="${MZRDS_INSTALL_DIR:-/usr/local/bin}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检测操作系统
detect_platform() {
    local os
    local arch
    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os" in
        Linux*)
            case "$arch" in
                x86_64) echo "linux-amd64" ;;
                # aarch64) echo "linux-arm64" ;;
                *) error "不支持的 Linux 架构: $arch" ;;
            esac
            ;;
        Darwin*)
            case "$arch" in
                x86_64) echo "macos-amd64" ;;
                arm64) echo "macos-arm64" ;;
                *) error "不支持的 macOS 架构: $arch" ;;
            esac
            ;;
        *)
            error "不支持的操作系统: $os"
            ;;
    esac
}

# 获取最新版本号
get_latest_version() {
    local api="https://api.github.com/repos/$REPO/releases/latest"
    local response

    if command -v curl &>/dev/null; then
        response=$(curl -fsSL "$api")
    elif command -v wget &>/dev/null; then
        response=$(wget -qO- "$api")
    else
        error "需要 curl 或 wget 命令"
    fi

    # 检查响应是否包含错误信息
    if echo "$response" | grep -q "Not Found\|API rate limit exceeded"; then
        error "API 响应错误: $response"
    fi

    # 使用更稳健的 JSON 解析方法
    if command -v jq &>/dev/null; then
        echo "$response" | jq -r '.tag_name'
    else
        # 后备方案：使用更精确的正则表达式
        echo "$response" | sed -n 's/.*"tag_name":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1
    fi
}

# 下载文件
download() {
    local url="$1"
    local output="$2"
    local status=0

    if command -v curl &>/dev/null; then
        curl -#fSL "$url" -o "$output" || status=$?
    elif command -v wget &>/dev/null; then
        wget -q --show-progress "$url" -O "$output" || status=$?
    else
        error "需要 curl 或 wget 命令"
    fi

    return $status
}

# 检查是否需要 sudo
need_sudo() {
    if [ -w "$INSTALL_DIR" ]; then
        echo ""
    else
        echo "sudo"
    fi
}

verify_checksum() {
    local binary="$1"
    local checksum_file="$2"
    local expected_sum
    local actual_sum

    # Extract just the hash from the checksum file (first field)
    expected_sum=$(awk '{print $1}' "$checksum_file")

    if command -v sha256sum &>/dev/null; then
        actual_sum=$(sha256sum "$binary" | awk '{print $1}')
    elif command -v shasum &>/dev/null; then
        actual_sum=$(shasum -a 256 "$binary" | awk '{print $1}')
    else
        warn "未找到 sha256sum/shasum，跳过校验"
        return 0
    fi

    if [ "$expected_sum" != "$actual_sum" ]; then
        echo "期望值: $expected_sum"
        echo "实际值: $actual_sum"
        return 1
    fi
}

# 主函数
main() {
    info "mzrds 安装程序"
    echo ""
    
    # 检测平台
    info "检测操作系统和架构..."
    PLATFORM=$(detect_platform)
    info "检测到平台: $PLATFORM"
    
    # 获取版本
    if [ "$VERSION" = "latest" ]; then
        info "获取最新版本信息..."
        VERSION=$(get_latest_version)
        if [ -z "$VERSION" ]; then
            error "无法获取最新版本信息"
        fi
    fi
    info "准备安装版本: $VERSION"

    # 选择安装目录
    echo ""
    echo "请选择安装位置 / Select installation directory:"
    echo "  1) 当前目录 / Current directory ($(pwd)) [Default]"
    echo "  2) 系统目录 / System directory (/usr/local/bin)"
    read -r -p "请输入选项 / Enter choice [1-2]: " choice_dir
    echo ""
    choice_dir=${choice_dir:-1}

    if [ "$choice_dir" = "2" ]; then
        INSTALL_DIR="/usr/local/bin"
    else
        INSTALL_DIR="$(pwd)"
    fi
    
    # 构建下载 URL
    BINARY_NAME="mzrds-$PLATFORM"
    
    # 尝试 GitHub 直连
    BASE_URL="https://github.com/$REPO/releases/download/$VERSION"
    DOWNLOAD_URL="$BASE_URL/$BINARY_NAME"
    

    
    # 创建临时目录
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT
    
    # 下载二进制文件
    info "正在下载 mzrds..."
    echo "URL: $DOWNLOAD_URL"
    
    if ! download "$DOWNLOAD_URL" "$TMP_DIR/mzrds"; then
        error "下载失败，请检查网络连接或版本号是否正确"
    fi

    # 下载校验文件（如果存在）
    if download "${DOWNLOAD_URL}.sha256" "$TMP_DIR/mzrds.sha256"; then
        info "验证文件完整性..."
        pushd "$TMP_DIR" >/dev/null
        if ! verify_checksum "mzrds" "mzrds.sha256"; then
            error "文件校验失败，请重试"
        fi
        popd >/dev/null
    else
        warn "未找到校验文件，跳过校验"
    fi
    
    # 添加执行权限
    chmod +x "$TMP_DIR/mzrds"
    
    # 安装
    SUDO=$(need_sudo)
    info "安装到 $INSTALL_DIR/mzrds..."
    
    if [ ! -d "$INSTALL_DIR" ]; then
        if [ -n "$SUDO" ]; then
            $SUDO mkdir -p "$INSTALL_DIR"
        else
            mkdir -p "$INSTALL_DIR"
        fi
    fi

    if [ -n "$SUDO" ]; then
        if [ "$INSTALL_DIR" = "/usr/local/bin" ]; then
             warn "需要管理员权限来安装到 $INSTALL_DIR"
        fi
        $SUDO mv "$TMP_DIR/mzrds" "$INSTALL_DIR/mzrds"
    else
        mv "$TMP_DIR/mzrds" "$INSTALL_DIR/mzrds"
    fi
    
    # 验证安装
    TARGET_BIN="$INSTALL_DIR/mzrds"
    if [ -f "$TARGET_BIN" ]; then
        info "✅ mzrds 安装成功！"
        echo ""
        
        # 尝试运行帮助命令
        if "$TARGET_BIN" --help >/dev/null 2>&1; then
             "$TARGET_BIN" --help | head -n 10
        else
             warn "无法运行二进制文件 (可能是架构不匹配: $PLATFORM)"
        fi
        echo ""

        # 添加到环境变量
        echo "是否自动添加到环境变量 PATH？/ Add to PATH?"
        read -r -p "请输入 [y/N]: " choice_path
        choice_path=${choice_path:-N}

        if [[ "$choice_path" =~ ^[Yy]$ ]]; then
            SHELL_RC=""
            case "$SHELL" in
                */zsh) SHELL_RC="$HOME/.zshrc" ;;
                */bash)
                    if [ -f "$HOME/.bash_profile" ]; then
                        SHELL_RC="$HOME/.bash_profile"
                    else
                        SHELL_RC="$HOME/.bashrc"
                    fi
                    ;;
                *) ;;
            esac

            if [ -n "$SHELL_RC" ]; then
                # 检查是否已经在 PATH 中
                if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
                    if ! grep -q "export PATH=.*$INSTALL_DIR" "$SHELL_RC"; then
                        echo "" >> "$SHELL_RC"
                        echo "# mzrds" >> "$SHELL_RC"
                        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
                        info "已添加到 $SHELL_RC"
                        info "请运行 'source $SHELL_RC' 生效"
                    else
                        warn "配置已存在于 $SHELL_RC"
                    fi
                else
                    warn "目录已在 PATH 中"
                fi
            else
                warn "未检测到支持的 Shell 配置文件 (bash/zsh)"
                echo "请手动添加: export PATH=\"\$PATH:$INSTALL_DIR\""
            fi
        fi

        echo ""
        info "安装完成 / Installation complete"
        info "可执行文件位置: $TARGET_BIN"
    else
        error "安装失败，文件未找到: $TARGET_BIN"
    fi
}

# 运行
main "$@"

