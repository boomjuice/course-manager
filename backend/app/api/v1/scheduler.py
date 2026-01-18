"""
定时任务管理 API - 仅管理员可用
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_admin_user
from app.core.scheduler import get_scheduler_status, run_task_manually
from app.models.user import User
from app.schemas.common import success_response

router = APIRouter(prefix="/scheduler", tags=["定时任务"])


@router.get("/status", summary="获取调度器状态")
async def scheduler_status(
    current_user: User = Depends(get_admin_user)
):
    """
    获取定时任务调度器状态

    - 需要管理员权限
    - 返回调度器运行状态和所有任务信息
    """
    return success_response(get_scheduler_status())


@router.post("/run/{task_id}", summary="手动执行定时任务")
async def run_task(
    task_id: str,
    current_user: User = Depends(get_admin_user)
):
    """
    手动执行指定的定时任务

    - 需要管理员权限
    - 可用任务ID: auto_complete_schedules (自动完成过期排课)
    """
    try:
        await run_task_manually(task_id)
        return success_response({
            "success": True,
            "message": f"任务 {task_id} 执行完成",
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")
