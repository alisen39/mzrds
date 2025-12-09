## mzrds

mzrds 是一个无需安装 redis-cli 即可连接 Redis 的命令行工具，基于 Python 3.13、Typer 与 redis-py 构建，并支持通过 uv 管理依赖与使用 PyInstaller 编译为单文件。

### 主要特性

- 与 redis-cli 兼容的连接参数（host、port、password、db、uri、tls 等）
- 配置文件（`~/.config/mzrds/config.toml`）保存多套连接方式，可快速切换
- 支持 TLS、用户名/密码、多数据库以及 Redis Cluster
- scan/hscan/sscan/zscan 支持 `--auto` 自动翻页
- `exec` 命令透传任意 Redis 命令
- PyInstaller 编译成可分发的 Linux / macOS 可执行文件

### 安装与使用

#### 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/alisen39/mzrds/master/install.sh | bash
# 或
wget -qO- https://raw.githubusercontent.com/alisen39/mzrds/master/install.sh | bash
```

安装脚本会自动：
- 检测平台（Linux/macOS + amd64/arm64）
- 获取最新 GitHub Release 二进制
- 验证 SHA256（若 release 提供校验文件）
- 安装到 `/usr/local/bin/mzrds`（可通过 `MZRDS_INSTALL_DIR` 自定义）

可用环境变量：
- `MZRDS_VERSION`：指定版本号（默认 latest）
- `MZRDS_REPO`：自定义仓库（默认 `alisen39/mzrds`）
- `MZRDS_INSTALL_DIR`：自定义安装目录（默认 `/usr/local/bin`）

#### 手动安装

```bash
# 以 v0.1.0 为例
wget https://github.com/alisen39/mzrds/releases/download/v0.1.0/mzrds-linux-amd64
chmod +x mzrds-linux-amd64
sudo mv mzrds-linux-amd64 /usr/local/bin/mzrds
```

Release 将提供以下构建产物：
- `mzrds-linux-amd64`
- `mzrds-macos-amd64`
- `mzrds-macos-arm64`

#### 运行示例

```bash
# Ping 默认本地 Redis
mzrds exec ping

# 保存连接配置
mzrds -h redis.example.com -a secret --tls config save prod

# 使用保存的 prod 配置执行命令
mzrds --use prod exec get mykey

# 自动翻页 zscan
mzrds --use prod zscan leaderboard --pattern "*" --auto
```

### 开发环境

```bash
# 安装依赖
uv sync

# 运行 CLI
uv run mzrds --help
```

### 测试

项目包含完整的测试套件，包括单元测试、集成测试和冒烟测试：

```bash
# 运行所有测试（需要 Redis 连接 192.168.31.12:6379）
uv run pytest tests/ -v -m ""

# 仅运行单元测试（不需要 Redis）
uv run pytest tests/ -v -m "not integration and not smoke"

# 仅运行集成测试（需要 Redis）
uv run pytest tests/ -v -m integration

# 运行冒烟测试和性能测试（需要 Redis，会生成大量数据）
uv run pytest tests/ -v -m smoke -s

# 或使用测试脚本
./run_tests.sh
```

测试覆盖：
- **单元测试**：配置管理（保存、读取、删除、切换）、命令执行器解码功能
- **集成测试**：Redis 客户端连接（普通模式、Cluster 模式、TLS）、基本操作（SET/GET、Hash、Set、Sorted Set）、Scan 命令（scan、hscan、sscan、zscan）及自动翻页
- **冒烟测试**：大数据集性能测试（10,000+ 条数据）、zscan 性能基准测试、不同 count 值的性能对比

**性能测试结果示例**（基于 10,000 条数据的 zscan）：
- `count=10`: ~1,800 条/秒
- `count=100`: ~12,800 条/秒
- `count=500`: ~31,400 条/秒
- `count=1000`: ~48,000 条/秒

### 编译发布

#### 本地编译

```bash
uv run python build.py
# dist/ 目录下生成对应平台的单文件可执行程序
```

#### 自动发布（推荐）

项目内置 GitHub Actions Workflow（`.github/workflows/release.yml`），当创建 `v*.*.*` 标签时会：
1. 在 macOS (amd64/arm64) 与 Ubuntu (amd64/arm64) 上并行构建
2. 运行单元测试（`pytest -m "not integration and not smoke"`）
3. 上传各平台二进制与 SHA256 校验文件
4. 自动创建 GitHub Release

**发布新版本的步骤：**

```bash
# 1. 确保代码已提交并推送到远程仓库
git add .
git commit -m "feat: 新功能描述"
git push origin master

# 2. 创建版本标签（遵循语义化版本，如 v0.1.0, v1.0.0）
git tag v0.1.0

# 3. 推送标签到远程仓库（这会触发 GitHub Actions 自动构建和发布）
git push origin v0.1.0

# 或者一次性推送所有标签
git push origin --tags
```

**注意事项：**
- 标签格式必须为 `v*.*.*`（如 `v0.1.0`、`v1.2.3`）
- 推送标签后，GitHub Actions 会自动开始构建流程
- 构建完成后会在 GitHub Releases 页面自动创建 Release
- Release 产物可搭配 `install.sh` 实现一键安装与升级

#### 手动触发发布

也可以通过 GitHub Actions 的 `workflow_dispatch` 手动触发发布：
1. 访问 GitHub 仓库的 Actions 页面
2. 选择 "Build and Release" workflow
3. 点击 "Run workflow"
4. 输入版本号（如 `v0.1.0`）
5. 点击 "Run workflow" 开始构建

