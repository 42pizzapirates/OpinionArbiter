from app.services.host.host_service import HostService
from app.services.realtime.broadcaster_service import BroadcasterService


class AppServiceEventCoordinator:
    """应用服务事件协调器：统一协调后台广播器与缓冲器的启动与销毁"""

    def __init__(self, host_service: HostService, broadcaster_service: BroadcasterService) -> None:
        """初始化协调器并注入依赖组件"""
        self.host_service = host_service
        self.broadcaster_service = broadcaster_service

    def register(self) -> None:
        """统一注册并启动所有关联的后台服务组件"""

        # 1. 启动前端实时广播服务
        self.broadcaster_service.register_broadcaster()
        # 2. 启动研判讨论缓冲服务
        self.host_service.register_discussion_buffer()

    def shutdown(self) -> None:
        """统一注销并停止所有关联的后台服务组件"""

        # 1. 停止广播服务，断开事件订阅
        self.broadcaster_service.stop_broadcaster()
        # 2. 停止讨论缓冲服务，释放监听
        self.host_service.stop_discussion_buffer()