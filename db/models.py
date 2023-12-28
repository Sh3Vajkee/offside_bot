from sqlalchemy import (BigInteger, Boolean, Column, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from db.base import Base


class Player(Base):
    __tablename__ = 'player'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))

    card_quants = Column(BigInteger, default=0)
    rating = Column(BigInteger, default=0)
    penalty_rating = Column(BigInteger, default=100)

    last_open = Column(BigInteger, default=0)

    transactions = Column(BigInteger, default=0)

    lucky_quants = Column(Integer, default=0)
    last_lucky = Column(BigInteger, default=0)

    joined_at_ts = Column(BigInteger, defaul=0)
    joined_at_txt = Column(String(50))

    usercards = relationship("UserCard", back_populates="player")


class CardItem(Base):
    __tablename__ = "carditem"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255))
    team = Column(String(255))
    nickname = Column(String(255))
    image = Column(String(255))
    rarity = Column(String(20))
    points = Column(Integer)


class UserCard(Base):
    __tablename__ = "usercard"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("player.id"))
    card_id = Column(Integer, ForeignKey("carditem.id", ondelete="CASCADE"))
    card_rarity = Column(String(20))
    points = Column(Integer)
    quant = Column(Integer, default=1)

    card = relationship("CardItem")
    player = relationship("Player", back_populates="usercards")
