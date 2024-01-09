from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Player


async def day_reset(db):
    ssn: AsyncSession
    async with db() as ssn:
        await ssn.execute(update(Player).filter(
            Player.leg_craft > 0).values(leg_craft=0))
        await ssn.commit()
