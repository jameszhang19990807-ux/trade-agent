"""
Celery tasks for async processing: follow-up reminders, batch jobs.
"""
from celery import Celery
from .config import settings

celery_app = Celery(
    "trade_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-dormant-leads": {
            "task": "app.tasks.check_dormant_leads",
            "schedule": 3600.0,  # Every hour
        },
        "send-followup-reminders": {
            "task": "app.tasks.send_followup_reminders",
            "schedule": 7200.0,  # Every 2 hours
        },
    },
)


@celery_app.task
def check_dormant_leads():
    """Mark leads as dormant if no contact for 7 days."""
    from datetime import datetime, timedelta
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from .models.customer import Customer

    async def _run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession)
        async with async_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=7)
            await db.execute(
                update(Customer)
                .where(Customer.pipeline_stage.in_(["replied", "deep_talk"]))
                .where(Customer.last_contact_at < cutoff)
                .values(pipeline_stage="dormant")
            )
            await db.commit()
        await engine.dispose()

    import asyncio
    asyncio.run(_run())


@celery_app.task
def send_followup_reminders():
    """Send follow-up template messages to dormant leads."""
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from .models.customer import Customer
    from .services.whatsapp import whatsapp_client

    async def _run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession)
        async with async_session() as db:
            cutoff = datetime.utcnow() - timedelta(hours=48)
            result = await db.execute(
                select(Customer)
                .where(Customer.pipeline_stage == "dormant")
                .where(Customer.last_contact_at < cutoff)
                .limit(10)
            )
            customers = result.scalars().all()
            for c in customers:
                try:
                    await whatsapp_client.send_template(
                        c.whatsapp_number,
                        "follow_up_inquiry",
                        "en",
                        [c.display_name],
                    )
                except Exception:
                    pass
        await engine.dispose()

    import asyncio
    asyncio.run(_run())
