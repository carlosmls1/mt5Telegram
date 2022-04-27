import pyrogram.raw.base
from pyrogram import Client

app = Client(
    "tg_account",
    api_id=17821682,
    api_hash="95ff2d4a2d3bb50a9ceb3404fce976ee"
)
with app:
    for dialog in app.get_dialogs():
        print(dialog.chat.title)
        print(dialog.chat.id)