#!/usr/bin/env python3
"""
Initialize system dictionaries.
"""
import asyncio
import sys
sys.path.insert(0, '..')

from app.database import async_session_maker, init_db
from app.models.dictionary import DictType, DictItem


INITIAL_DICTS = [
    {
        "code": "gender",
        "name": "性别",
        "is_system": True,
        "items": [
            {"value": "male", "label": "男", "color": "#3B82F6"},
            {"value": "female", "label": "女", "color": "#EC4899"},
        ]
    },
    {
        "code": "student_status",
        "name": "学生状态",
        "is_system": True,
        "items": [
            {"value": "active", "label": "在读", "color": "#10B981", "is_default": True},
            {"value": "suspended", "label": "休学", "color": "#F59E0B"},
            {"value": "graduated", "label": "结业", "color": "#6B7280"},
            {"value": "dropped", "label": "退学", "color": "#EF4444"},
        ]
    },
    {
        "code": "teacher_status",
        "name": "教师状态",
        "is_system": True,
        "items": [
            {"value": "active", "label": "在职", "color": "#10B981", "is_default": True},
            {"value": "leave", "label": "请假", "color": "#F59E0B"},
            {"value": "resigned", "label": "离职", "color": "#6B7280"},
        ]
    },
    {
        "code": "subject",
        "name": "学科",
        "is_system": True,
        "items": [
            {"value": "chinese", "label": "语文", "color": "#EF4444"},
            {"value": "math", "label": "数学", "color": "#3B82F6"},
            {"value": "english", "label": "英语", "color": "#10B981"},
            {"value": "physics", "label": "物理", "color": "#8B5CF6"},
            {"value": "chemistry", "label": "化学", "color": "#F59E0B"},
            {"value": "biology", "label": "生物", "color": "#06B6D4"},
            {"value": "politics", "label": "政治", "color": "#EC4899"},
            {"value": "history", "label": "历史", "color": "#84CC16"},
            {"value": "geography", "label": "地理", "color": "#F97316"},
        ]
    },
    {
        "code": "course_level",
        "name": "课程难度",
        "is_system": True,
        "items": [
            {"value": "beginner", "label": "入门", "color": "#10B981"},
            {"value": "intermediate", "label": "进阶", "color": "#3B82F6"},
            {"value": "advanced", "label": "高级", "color": "#8B5CF6"},
        ]
    },
    {
        "code": "grade",
        "name": "年级",
        "is_system": True,
        "items": [
            {"value": "preschool", "label": "学前"},
            {"value": "g1", "label": "一年级"},
            {"value": "g2", "label": "二年级"},
            {"value": "g3", "label": "三年级"},
            {"value": "g4", "label": "四年级"},
            {"value": "g5", "label": "五年级"},
            {"value": "g6", "label": "六年级"},
            {"value": "g7", "label": "初一"},
            {"value": "g8", "label": "初二"},
            {"value": "g9", "label": "初三"},
            {"value": "g10", "label": "高一"},
            {"value": "g11", "label": "高二"},
            {"value": "g12", "label": "高三"},
            {"value": "adult", "label": "成人"},
        ]
    },
    {
        "code": "student_source",
        "name": "学生来源",
        "is_system": True,
        "items": [
            {"value": "referral", "label": "老学员推荐", "is_default": True},
            {"value": "online", "label": "网络推广"},
            {"value": "offline", "label": "线下推广"},
            {"value": "walk_in", "label": "自然到访"},
            {"value": "other", "label": "其他"},
        ]
    },
    {
        "code": "education",
        "name": "学历",
        "is_system": True,
        "items": [
            {"value": "high_school", "label": "高中"},
            {"value": "college", "label": "大专"},
            {"value": "bachelor", "label": "本科"},
            {"value": "master", "label": "硕士"},
            {"value": "doctor", "label": "博士"},
        ]
    },
    {
        "code": "class_status",
        "name": "开班状态",
        "is_system": True,
        "items": [
            {"value": "pending", "label": "待开班", "color": "#6B7280"},
            {"value": "ongoing", "label": "进行中", "color": "#10B981"},
            {"value": "completed", "label": "已结束", "color": "#3B82F6"},
            {"value": "cancelled", "label": "已取消", "color": "#EF4444"},
        ]
    },
    # 学生标签相关字典
    {
        "code": "student_level",
        "name": "学生水平",
        "is_system": True,
        "items": [
            {"value": "excellent", "label": "优秀", "color": "#10B981"},
            {"value": "good", "label": "良好", "color": "#3B82F6"},
            {"value": "average", "label": "中等", "color": "#F59E0B"},
            {"value": "weak", "label": "薄弱", "color": "#EF4444"},
        ]
    },
    {
        "code": "learning_goal",
        "name": "学习目标",
        "is_system": True,
        "items": [
            {"value": "competition", "label": "竞赛冲刺", "color": "#8B5CF6"},
            {"value": "advanced", "label": "培优拔高", "color": "#3B82F6"},
            {"value": "consolidate", "label": "巩固提升", "color": "#10B981"},
            {"value": "basic", "label": "基础补差", "color": "#F59E0B"},
            {"value": "interest", "label": "兴趣培养", "color": "#EC4899"},
        ]
    },
    {
        "code": "grade_stage",
        "name": "学段",
        "is_system": True,
        "items": [
            {"value": "primary", "label": "小学", "color": "#10B981"},
            {"value": "junior", "label": "初中", "color": "#3B82F6"},
            {"value": "senior", "label": "高中", "color": "#8B5CF6"},
        ]
    },
]


async def init_dictionaries():
    """Initialize system dictionaries."""
    await init_db()

    async with async_session_maker() as session:
        from sqlalchemy import select

        for dict_data in INITIAL_DICTS:
            # Check if exists
            result = await session.execute(
                select(DictType).where(DictType.code == dict_data["code"])
            )
            if result.scalar_one_or_none():
                print(f"Dictionary '{dict_data['code']}' already exists, skipping...")
                continue

            # Create type
            dict_type = DictType(
                code=dict_data["code"],
                name=dict_data["name"],
                is_system=dict_data.get("is_system", False),
                is_active=True,
                created_by="system",
            )

            # Create items
            for i, item_data in enumerate(dict_data.get("items", [])):
                item = DictItem(
                    value=item_data["value"],
                    label=item_data["label"],
                    color=item_data.get("color"),
                    is_default=item_data.get("is_default", False),
                    is_active=True,
                    sort_order=i,
                    created_by="system",
                )
                dict_type.items.append(item)

            session.add(dict_type)
            print(f"Created dictionary: {dict_data['name']} ({dict_data['code']})")

        await session.commit()

    print("\n" + "=" * 50)
    print("Dictionary initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(init_dictionaries())
