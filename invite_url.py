import asyncio
import typing

import pyrogram

class Channel:
    def __init__(self, session_file_name: str):
        self.api_id: int = 2225296
        self.api_hash: str = '52d6315ad5979dd1dc932f1627320d4c'
        self.name: str = session_file_name
        self.chat_id: str or int = -1001962381384

    async def create_link(self) -> str:
        async with pyrogram.Client(api_id=self.api_id, api_hash=self.api_hash, name=self.name) as app:
            obj_link: pyrogram.types.ChatInviteLink = await app.create_chat_invite_link(self.chat_id)
            return obj_link.invite_link

    async def get_link_count_join(self, link: str) -> int:
        async with pyrogram.Client(api_id=self.api_id, api_hash=self.api_hash, name=self.name) as app:
            obj_link: pyrogram.types.ChatInviteLink = await app.get_chat_invite_link(self.chat_id, link)
            return obj_link.member_count


# info = asyncio.run(Channel("rolakov").get_link_count_join('https://t.me/+KhNFXe6DwGEwZTIy'))
# new_link = asyncio.run(Channel('rolakov').create_link())
#
# print(info)
# print(new_link)