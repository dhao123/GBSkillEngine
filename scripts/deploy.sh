#!/bin/bash
# GBSkillEngine 部署脚本

set -e

# 获取脚本所在目录，然后切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    echo "GBSkillEngine 部署脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  dev         启动开发环境"
    echo "  prod        启动生产环境"
    echo "  stop        停止所有服务"
    echo "  restart     重启所有服务"
    echo "  logs        查看服务日志"
    echo "  status      查看服务状态"
    echo "  clean       清理容器和卷"
    echo "  migrate     运行数据库迁移"
    echo "  shell       进入后端容器shell"
    echo ""
    echo "选项:"
    echo "  -h, --help  显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev              # 启动开发环境"
    echo "  $0 prod             # 启动生产环境"
    echo "  $0 logs backend     # 查看后端日志"
}

# 检查.env文件
check_env() {
    if [ ! -f ".env" ]; then
        warn ".env 文件不存在，从 .env.example 创建..."
        cp .env.example .env
        info ".env 文件已创建，请根据需要修改配置"
    fi
}

# 启动开发环境
start_dev() {
    info "启动开发环境..."
    check_env
    docker-compose up -d
    info "开发环境已启动"
    info "前端: http://localhost:5173"
    info "后端: http://localhost:8000"
    info "API文档: http://localhost:8000/docs"
    info "Neo4j: http://localhost:7474"
}

# 启动生产环境
start_prod() {
    info "启动生产环境..."
    check_env
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    info "生产环境已启动"
}

# 停止服务
stop_services() {
    info "停止所有服务..."
    docker-compose down
    info "服务已停止"
}

# 重启服务
restart_services() {
    info "重启所有服务..."
    docker-compose restart
    info "服务已重启"
}

# 查看日志
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# 查看状态
view_status() {
    docker-compose ps
}

# 清理
clean_all() {
    warn "这将删除所有容器、网络和卷数据！"
    read -p "确定要继续吗? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        info "清理完成"
    else
        info "操作已取消"
    fi
}

# 运行迁移
run_migrate() {
    info "运行数据库迁移..."
    docker-compose exec backend alembic upgrade head
    info "迁移完成"
}

# 进入shell
enter_shell() {
    docker-compose exec backend /bin/bash
}

# 主函数
main() {
    case "${1:-}" in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "$2"
            ;;
        status)
            view_status
            ;;
        clean)
            clean_all
            ;;
        migrate)
            run_migrate
            ;;
        shell)
            enter_shell
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

main "$@"
