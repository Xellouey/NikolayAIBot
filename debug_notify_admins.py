import asyncio
import datetime
import handlers.support as s

# Monkeypatch bot.send_message
sent_to = []
async def fake_send_message(admin_id, text):
    sent_to.append(int(admin_id))

s.bot.send_message = fake_send_message

class T:
    pass
class U:
    pass

t = T()
t.id = 999
t.user_id = 123456
t.subject = 'Test'
t.created_at = datetime.datetime.now()

u = U()
u.full_name = 'User'

async def main():
    await s.notify_admins_new_ticket(t, u)
    print({'sent_to': sent_to})

if __name__ == '__main__':
    asyncio.run(main())

