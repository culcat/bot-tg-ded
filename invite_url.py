import typing

import pyrogram

class Channel:
    def __init__(self, session_file_name: str):
        self.api_id: int = 2225296
        self.api_hash: str = '52d6315ad5979dd1dc932f1627320d4c'
        self.name: str = session_file_name
        self.chat_id: str or int = -1001962381384

    def create_link(self):
        with pyrogram.Client(api_id=self.api_id, api_hash=self.api_hash, name=self.name) as app:
            return app.create_chat_invite_link(self.chat_id)

    def get_link_info(self, link: str):
        with pyrogram.Client(api_id=self.api_id, api_hash=self.api_hash, name=self.name) as app:
            return app.get_chat_invite_link(self.chat_id, link)


info = Channel().get_link_info('https://t.me/+KhNFXe6DwGEwZTIy')
# new_link = Channel().create_link()

print(1)