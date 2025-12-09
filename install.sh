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
        curl -fsSL "$url" -o "$output" || status=$?
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

    if command -v sha256sum &>/dev/null; then
        sha256sum --check --status "$checksum_file"
    elif command -v shasum &>/dev/null; then
        (cd "$(dirname "$checksum_file")" && shasum -a 256 -c "$(basename "$checksum_file")" >/dev/null)
    else
        warn "未找到 sha256sum/shasum，跳过校验"
        return 0
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
    
    # 构建下载 URL
    BINARY_NAME="mzrds-$PLATFORM"
    
    # 尝试 GitHub 直连
    BASE_URL="https://github.com/$REPO/releases/download/$VERSION"
    DOWNLOAD_URL="$BASE_URL/$BINARY_NAME"
    
    # 检测是否需要使用镜像
    if command -v curl &>/dev/null; then
        if ! curl -m 3 -s https://github.com >/dev/null 2>&1; then
            warn "GitHub 访问较慢，使用镜像加速..."
            BASE_URL="https://ghproxy.com/https://github.com/$REPO/releases/download/$VERSION"
            DOWNLOAD_URL="$BASE_URL/$BINARY_NAME"
        fi
    fi
    
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
    
    if [ -n "$SUDO" ]; then
        warn "需要管理员权限来安装到 $INSTALL_DIR"
        $SUDO mv "$TMP_DIR/mzrds" "$INSTALL_DIR/mzrds"
    else
        mv "$TMP_DIR/mzrds" "$INSTALL_DIR/mzrds"
    fi
    
    # 验证安装
    if command -v mzrds &> /dev/null; then
        info "✅ mzrds 安装成功！"
        echo ""
        mzrds --help | head -n 10
        echo ""
        info "运行 'mzrds --help' 查看完整帮助"
        info "运行 'mzrds -h 127.0.0.1 exec ping' 测试连接"
    else
        error "安装失败，请检查 $INSTALL_DIR 是否在 PATH 中"
    fi
}

# 运行
main "$@"

