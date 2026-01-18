"""
Seed script - 生成测试数据
Run: cd backend && python scripts/seed_data.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, time, timedelta
from decimal import Decimal
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.campus import Campus, Classroom
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.class_plan import ClassPlan
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule


async def seed_campuses(db):
    """创建校区和教室"""
    print("📍 创建校区和教室...")

    campuses_data = [
        {
            "name": "总部校区",
            "address": "北京市海淀区中关村大街1号",
            "phone": "010-12345678",
            "contact_person": "张主任",
            "description": "总部旗舰校区，设施齐全",
            "classrooms": [
                {"name": "101教室", "capacity": 30},
                {"name": "102教室", "capacity": 25},
                {"name": "201多媒体室", "capacity": 40},
                {"name": "202小班教室", "capacity": 15},
            ]
        },
        {
            "name": "朝阳分校",
            "address": "北京市朝阳区建国路88号",
            "phone": "010-87654321",
            "contact_person": "李校长",
            "description": "朝阳区重点分校",
            "classrooms": [
                {"name": "A101", "capacity": 35},
                {"name": "A102", "capacity": 30},
                {"name": "B201舞蹈室", "capacity": 20},
            ]
        },
        {
            "name": "西城教学点",
            "address": "北京市西城区西单北大街100号",
            "phone": "010-55556666",
            "contact_person": "王老师",
            "description": "西城便民教学点",
            "classrooms": [
                {"name": "1号教室", "capacity": 20},
                {"name": "2号教室", "capacity": 20},
            ]
        },
    ]

    created_campuses = []
    for i, data in enumerate(campuses_data):
        campus = Campus(
            name=data["name"],
            address=data["address"],
            phone=data["phone"],
            contact_person=data["contact_person"],
            description=data["description"],
            is_active=True,
            sort_order=i,
            created_by="system",
        )
        db.add(campus)
        await db.flush()

        for j, cr in enumerate(data["classrooms"]):
            classroom = Classroom(
                campus_id=campus.id,
                name=cr["name"],
                capacity=cr["capacity"],
                is_active=True,
                sort_order=j,
                created_by="system",
            )
            db.add(classroom)

        created_campuses.append(campus)

    await db.flush()
    print(f"  ✅ 创建了 {len(created_campuses)} 个校区")
    return created_campuses


async def seed_courses(db):
    """创建课程产品"""
    print("📚 创建课程产品...")

    courses_data = [
        {"name": "少儿编程入门", "code": "CODE001", "category": "编程", "level": "初级", "unit_price": 100, "target_audience": "6-10岁儿童"},
        {"name": "Python基础班", "code": "CODE002", "category": "编程", "level": "初级", "unit_price": 100, "target_audience": "10-15岁青少年"},
        {"name": "Python进阶班", "code": "CODE003", "category": "编程", "level": "中级", "unit_price": 120, "target_audience": "有Python基础的学员"},
        {"name": "少儿英语启蒙", "code": "ENG001", "category": "英语", "level": "初级", "unit_price": 120, "target_audience": "4-6岁儿童"},
        {"name": "剑桥少儿英语", "code": "ENG002", "category": "英语", "level": "中级", "unit_price": 140, "target_audience": "7-12岁儿童"},
        {"name": "数学思维训练", "code": "MATH001", "category": "数学", "level": "初级", "unit_price": 100, "target_audience": "5-8岁儿童"},
        {"name": "奥数竞赛班", "code": "MATH002", "category": "数学", "level": "高级", "unit_price": 150, "target_audience": "小学3-6年级"},
        {"name": "美术基础班", "code": "ART001", "category": "艺术", "level": "初级", "unit_price": 100, "target_audience": "5-12岁儿童"},
        {"name": "钢琴入门", "code": "MUSIC001", "category": "音乐", "level": "初级", "unit_price": 150, "target_audience": "5岁以上"},
        {"name": "机器人编程", "code": "ROBOT001", "category": "编程", "level": "中级", "unit_price": 140, "target_audience": "8-14岁青少年"},
    ]

    created_courses = []
    for i, data in enumerate(courses_data):
        course = Course(
            name=data["name"],
            code=data["code"],
            category=data["category"],
            level=data["level"],
            unit_price=Decimal(str(data["unit_price"])),
            target_audience=data["target_audience"],
            description=f"{data['name']}课程，适合{data['target_audience']}",
            objectives=f"掌握{data['name']}核心知识，培养学习兴趣",
            is_active=True,
            sort_order=i,
            created_by="system",
        )
        db.add(course)
        created_courses.append(course)

    await db.flush()
    print(f"  ✅ 创建了 {len(created_courses)} 个课程产品")
    return created_courses


async def seed_teachers(db):
    """创建教师"""
    print("👨‍🏫 创建教师...")

    teachers_data = [
        {"name": "张明", "gender": "male", "phone": "13800001001", "specialties": "Python,少儿编程", "education": "硕士"},
        {"name": "李芳", "gender": "female", "phone": "13800001002", "specialties": "英语", "education": "本科"},
        {"name": "王强", "gender": "male", "phone": "13800001003", "specialties": "数学,奥数", "education": "硕士"},
        {"name": "赵雪", "gender": "female", "phone": "13800001004", "specialties": "美术,书法", "education": "本科"},
        {"name": "刘洋", "gender": "male", "phone": "13800001005", "specialties": "钢琴,音乐理论", "education": "本科"},
        {"name": "陈静", "gender": "female", "phone": "13800001006", "specialties": "英语,剑桥少儿", "education": "硕士"},
        {"name": "周杰", "gender": "male", "phone": "13800001007", "specialties": "机器人,编程", "education": "本科"},
        {"name": "吴敏", "gender": "female", "phone": "13800001008", "specialties": "数学思维", "education": "本科"},
    ]

    created_teachers = []
    for data in teachers_data:
        teacher = Teacher(
            name=data["name"],
            gender=data["gender"],
            phone=data["phone"],
            specialties=data["specialties"],
            education=data["education"],
            introduction=f"{data['name']}老师，{data['education']}学历，擅长{data['specialties']}教学",
            is_active=True,
            created_by="system",
        )
        db.add(teacher)
        created_teachers.append(teacher)

    await db.flush()
    print(f"  ✅ 创建了 {len(created_teachers)} 个教师")
    return created_teachers


async def seed_students(db):
    """创建学生"""
    print("👦 创建学生...")

    first_names = ["小明", "小红", "小刚", "小丽", "小华", "小芳", "小强", "小美", "小龙", "小凤"]
    last_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
    schools = ["北京小学", "实验小学", "中关村一小", "朝阳外国语", "西城育才"]
    grades = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
    sources = ["朋友推荐", "网络广告", "地推活动", "老学员介绍", "自然进店"]

    created_students = []
    for i in range(25):
        name = random.choice(last_names) + random.choice(first_names)
        phone = f"138{random.randint(10000000, 99999999)}"
        parent_phone = f"139{random.randint(10000000, 99999999)}"

        student = Student(
            name=name,
            gender=random.choice(["male", "female"]),
            phone=phone,
            parent_name=f"{name[0]}爸爸" if random.random() > 0.5 else f"{name[0]}妈妈",
            parent_phone=parent_phone,
            school=random.choice(schools),
            grade=random.choice(grades),
            birthday=date(2015 + random.randint(0, 5), random.randint(1, 12), random.randint(1, 28)),
            source=random.choice(sources),
            status="active",
            is_active=True,
            remaining_hours=Decimal(str(random.randint(0, 50))),
            total_paid=Decimal(str(random.randint(0, 20000))),
            remark=f"学员{i+1}备注信息",
            created_by="system",
        )
        db.add(student)
        created_students.append(student)

    await db.flush()
    print(f"  ✅ 创建了 {len(created_students)} 个学生")
    return created_students


async def seed_class_plans(db, courses, teachers, campuses):
    """创建开班计划"""
    print("📋 创建开班计划...")

    # Get classrooms
    result = await db.execute(select(Classroom))
    classrooms = list(result.scalars().all())

    class_plans = []
    today = date.today()

    plan_configs = [
        {"course_idx": 0, "name": "2024秋季少儿编程A班", "status": "ongoing", "start_offset": -30},
        {"course_idx": 0, "name": "2024秋季少儿编程B班", "status": "ongoing", "start_offset": -20},
        {"course_idx": 1, "name": "Python基础周末班", "status": "ongoing", "start_offset": -45},
        {"course_idx": 2, "name": "Python进阶强化班", "status": "pending", "start_offset": 15},
        {"course_idx": 3, "name": "英语启蒙晚班", "status": "ongoing", "start_offset": -60},
        {"course_idx": 4, "name": "剑桥少儿英语Level1", "status": "ongoing", "start_offset": -30},
        {"course_idx": 5, "name": "数学思维周六班", "status": "ongoing", "start_offset": -40},
        {"course_idx": 6, "name": "奥数竞赛冲刺班", "status": "pending", "start_offset": 7},
        {"course_idx": 7, "name": "美术基础周日班", "status": "ongoing", "start_offset": -25},
        {"course_idx": 8, "name": "钢琴入门一对一", "status": "ongoing", "start_offset": -50},
        {"course_idx": 9, "name": "机器人编程寒假班", "status": "pending", "start_offset": 30},
        {"course_idx": 1, "name": "Python基础暑期班", "status": "completed", "start_offset": -120},
    ]

    for i, config in enumerate(plan_configs):
        course = courses[config["course_idx"]]
        teacher = teachers[i % len(teachers)]
        campus = campuses[i % len(campuses)]
        campus_classrooms = [c for c in classrooms if c.campus_id == campus.id]
        classroom = campus_classrooms[i % len(campus_classrooms)] if campus_classrooms else None

        start_date = today + timedelta(days=config["start_offset"])
        end_date = start_date + timedelta(days=90)

        plan = ClassPlan(
            name=config["name"],
            course_id=course.id,
            teacher_id=teacher.id,
            campus_id=campus.id,
            classroom_id=classroom.id if classroom else None,
            start_date=start_date,
            end_date=end_date,
            max_students=random.randint(15, 30),
            current_students=0,
            total_lessons=20,  # 默认20节课，price/total_hours已从Course移除
            completed_lessons=random.randint(0, 10) if config["status"] == "ongoing" else 0,
            status=config["status"],
            description=f"{config['name']}，由{teacher.name}老师授课",
            is_active=True,
            created_by="system",
        )
        db.add(plan)
        class_plans.append(plan)

    await db.flush()
    print(f"  ✅ 创建了 {len(class_plans)} 个开班计划")
    return class_plans


async def seed_enrollments(db, students, class_plans):
    """创建报名记录"""
    print("📝 创建报名记录...")

    enrollments = []
    for plan in class_plans:
        if plan.status in ["ongoing", "completed"]:
            # 每个班级随机报名5-12个学生
            enrolled_students = random.sample(students, min(random.randint(5, 12), len(students)))
            for student in enrolled_students:
                enrollment = Enrollment(
                    student_id=student.id,
                    class_plan_id=plan.id,
                    enroll_date=plan.start_date - timedelta(days=random.randint(1, 14)),
                    paid_amount=Decimal(str(random.randint(3000, 8000))),
                    purchased_hours=Decimal(str(random.randint(20, 60))),
                    used_hours=Decimal(str(random.randint(0, 20))),
                    status="active",
                    notes=f"报名{plan.name}",
                    created_by="system",
                )
                db.add(enrollment)
                enrollments.append(enrollment)

            # 更新班级人数
            plan.current_students = len(enrolled_students)

    await db.flush()
    print(f"  ✅ 创建了 {len(enrollments)} 条报名记录")
    return enrollments


async def seed_schedules(db, class_plans):
    """创建排课记录"""
    print("📅 创建排课记录...")

    # Get classrooms
    result = await db.execute(select(Classroom))
    classrooms = list(result.scalars().all())

    schedules = []
    today = date.today()

    time_slots = [
        (time(9, 0), time(11, 0)),
        (time(14, 0), time(16, 0)),
        (time(16, 30), time(18, 30)),
        (time(19, 0), time(21, 0)),
    ]

    for plan in class_plans:
        if plan.status in ["ongoing", "pending"]:
            campus_classrooms = [c for c in classrooms if c.campus_id == plan.campus_id]
            classroom = campus_classrooms[0] if campus_classrooms else None

            # 为每个班级创建未来2周的排课
            for week in range(2):
                # 每周2-3次课
                days = random.sample([0, 1, 2, 3, 4, 5, 6], random.randint(2, 3))
                for day in days:
                    schedule_date = today + timedelta(days=week * 7 + day)
                    if schedule_date < plan.start_date:
                        continue

                    slot = random.choice(time_slots)
                    schedule = Schedule(
                        class_plan_id=plan.id,
                        teacher_id=plan.teacher_id,
                        classroom_id=classroom.id if classroom else None,
                        schedule_date=schedule_date,
                        start_time=slot[0],
                        end_time=slot[1],
                        lesson_hours=Decimal("2.0"),
                        title=plan.name,
                        status="scheduled" if schedule_date >= today else "completed",
                        created_by="system",
                    )
                    db.add(schedule)
                    schedules.append(schedule)

    await db.flush()
    print(f"  ✅ 创建了 {len(schedules)} 条排课记录")
    return schedules


async def main():
    print("=" * 50)
    print("🚀 开始生成测试数据...")
    print("=" * 50)

    # Initialize database
    await init_db()

    async with async_session_maker() as db:
        try:
            # Check if data already exists
            result = await db.execute(select(Campus))
            if result.scalars().first():
                print("⚠️  数据库已有数据，跳过生成")
                print("   如需重新生成，请先清空相关表")
                return

            # Seed data in order
            campuses = await seed_campuses(db)
            courses = await seed_courses(db)
            teachers = await seed_teachers(db)
            students = await seed_students(db)
            class_plans = await seed_class_plans(db, courses, teachers, campuses)
            await seed_enrollments(db, students, class_plans)
            await seed_schedules(db, class_plans)

            await db.commit()

            print("=" * 50)
            print("✅ 测试数据生成完成！")
            print("=" * 50)

        except Exception as e:
            await db.rollback()
            print(f"❌ 生成失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
