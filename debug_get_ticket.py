import asyncio
from database.support import SupportTicket

async def main():
    st = SupportTicket()
    # Try the latest 5 tickets
    for ticket_id in [1,2,3,4,5,6,7,8]:
        t = await st.get_ticket(ticket_id)
        if t is None:
            print(ticket_id, '-> NONE')
        else:
            print(ticket_id, '->', t.id, t.user_id, t.subject, t.status)

if __name__ == '__main__':
    asyncio.run(main())

