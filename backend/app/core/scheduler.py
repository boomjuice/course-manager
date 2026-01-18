"""
定时任务调度器 - 使用 APScheduler 实现
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.schedule import Schedule
from app.models.enrollment import Enrollment
from app.models.lesson_record import LessonRecord
from app.models.class_plan import ClassPlan

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler: Optional[AsyncIOScheduler] = None


def _get_scheduler_session():
    """
    为调度器创建独立的数据库会话工厂
    避免 event loop 冲突问题
    """
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)


async def auto_complete_schedules():
    """
    自动完成过期排课任务
    把昨天及之前的 scheduled 状态排课自动标记为 completed
    并触发课时消耗记录
    """
    logger.info("开始执行自动完成排课任务...")

    # 使用独立的数据库会话，避免 event loop 问题
    Session = _get_scheduler_session()

    async with Session() as db:
        try:
            # 查找所有过期但未完成的排课（昨天及之前的 scheduled 状态）
            yesterday = date.today() - timedelta(days=1)

            result = await db.execute(
                select(Schedule).where(
                    Schedule.schedule_date <= yesterday,
                    Schedule.status == "scheduled"
                )
            )
            pending_schedules = list(result.scalars().all())

            if not pending_schedules:
                logger.info("没有需要自动完成的排课")
                return

            logger.info(f"找到 {len(pending_schedules)} 个待自动完成的排课")

            completed_count = 0
            error_count = 0

            for schedule in pending_schedules:
                try:
                    # 获取该班级所有在读报名
                    result = await db.execute(
                        select(Enrollment)
                        .options(selectinload(Enrollment.student))
                        .where(
                            Enrollment.class_plan_id == schedule.class_plan_id,
                            Enrollment.status == "active"
                        )
                    )
                    enrollments = list(result.scalars().all())

                    hours = Decimal(str(schedule.lesson_hours))
                    records_created = 0

                    for enrollment in enrollments:
                        # 创建消耗记录
                        record = LessonRecord(
                            enrollment_id=enrollment.id,
                            schedule_id=schedule.id,
                            record_date=schedule.schedule_date,
                            hours=hours,
                            type="schedule",
                            notes=f"排课消耗: {schedule.title or '课程'}",
                            created_by="system_scheduler",
                        )
                        db.add(record)
                        records_created += 1

                        # 更新报名已用课时
                        enrollment.used_hours = Decimal(str(enrollment.used_hours or 0)) + hours

                        # 更新学生剩余课时
                        if enrollment.student:
                            enrollment.student.remaining_hours = max(
                                Decimal("0"),
                                Decimal(str(enrollment.student.remaining_hours or 0)) - hours
                            )

                    # 更新排课状态为已完成
                    schedule.status = "completed"
                    schedule.updated_by = "system_scheduler"

                    completed_count += 1
                    logger.info(
                        f"排课 #{schedule.id} ({schedule.schedule_date}) 已自动完成，"
                        f"创建了 {records_created} 条课时消耗记录"
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(f"处理排课 #{schedule.id} 时出错: {str(e)}")
                    continue

            await db.commit()
            logger.info(
                f"自动完成排课任务执行完毕: "
                f"成功 {completed_count} 个, 失败 {error_count} 个"
            )

        except Exception as e:
            logger.error(f"自动完成排课任务执行失败: {str(e)}")
            await db.rollback()
            raise


async def auto_complete_class_plans():
    """
    自动结班任务
    把结班日期已过的开班计划自动标记为 completed（已结班）
    """
    logger.info("开始执行自动结班任务...")

    Session = _get_scheduler_session()

    async with Session() as db:
        try:
            yesterday = date.today() - timedelta(days=1)

            # 查找所有结班日期已过但状态还是 enrolling 或 in_progress 的开班计划
            result = await db.execute(
                select(ClassPlan).where(
                    ClassPlan.end_date <= yesterday,
                    ClassPlan.status.in_(["enrolling", "in_progress"]),
                    ClassPlan.is_active == True,
                )
            )
            pending_plans = list(result.scalars().all())

            if not pending_plans:
                logger.info("没有需要自动结班的开班计划")
                return

            logger.info(f"找到 {len(pending_plans)} 个待自动结班的开班计划")

            for plan in pending_plans:
                plan.status = "completed"
                plan.updated_by = "system_scheduler"
                logger.info(f"开班计划 #{plan.id} ({plan.name}) 已自动结班")

            await db.commit()
            logger.info(f"自动结班任务执行完毕: 成功 {len(pending_plans)} 个")

        except Exception as e:
            logger.error(f"自动结班任务执行失败: {str(e)}")
            await db.rollback()
            raise


def init_scheduler():
    """初始化定时任务调度器"""
    global scheduler

    if scheduler is not None:
        logger.warning("调度器已经初始化过了")
        return scheduler

    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # 每天凌晨 2:00 执行自动完成排课任务
    # 选择凌晨2点是因为这个时间段用户活动最少，不影响正常使用
    scheduler.add_job(
        auto_complete_schedules,
        trigger=CronTrigger(hour=2, minute=0),
        id="auto_complete_schedules",
        name="自动完成过期排课并扣课时",
        replace_existing=True,
    )

    # 每天凌晨 2:05 执行自动结班任务
    scheduler.add_job(
        auto_complete_class_plans,
        trigger=CronTrigger(hour=2, minute=5),
        id="auto_complete_class_plans",
        name="自动结班过期开班计划",
        replace_existing=True,
    )

    logger.info("定时任务调度器初始化完成")
    logger.info("已注册任务: 每天 02:00 自动完成过期排课, 02:05 自动结班")

    return scheduler


def start_scheduler():
    """启动调度器"""
    global scheduler

    if scheduler is None:
        scheduler = init_scheduler()

    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")
    else:
        logger.warning("调度器已在运行中")


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")

    scheduler = None


async def run_task_manually(task_id: str):
    """
    手动执行某个定时任务（用于测试或紧急情况）
    """
    if task_id == "auto_complete_schedules":
        await auto_complete_schedules()
    elif task_id == "auto_complete_class_plans":
        await auto_complete_class_plans()
    else:
        raise ValueError(f"未知的任务ID: {task_id}")


def get_scheduler_status():
    """获取调度器状态"""
    global scheduler

    if scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        # APScheduler 3.x 的 job 属性
        next_run = getattr(job, 'next_run_time', None)
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(next_run) if next_run else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": scheduler.running,
        "jobs": jobs,
    }
