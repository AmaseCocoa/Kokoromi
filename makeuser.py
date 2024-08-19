import asyncio

import bcrypt
from python_aid.aidx import genAidx

from prisma import Prisma


async def main(name: str, mail: str, displayName: str, description: str, password: str, isAdmin: bool=False) -> None:
    prisma = Prisma()
    salt = bcrypt.gensalt(rounds=10, prefix=b"2a")
    await prisma.connect()
    await prisma.author.create(
        data={
            "id": genAidx(),
            "name": name,
            "mail": mail,
            "displayName": displayName,
            "description": description,
            "password": bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8"),
            "isAdmin": isAdmin,
        }
    )
    await prisma.disconnect()


asyncio.run(main())
