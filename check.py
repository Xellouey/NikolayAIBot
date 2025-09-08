import asyncio
import logging
import time
import aioschedule as schedule
from database import mail


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    filename='file.log'
)

m = mail.Mail()


async def checkMail():
    """Check and process pending mails with improved logging"""
    mails = await m.get_wait_mails()
    
    if mails:
        logging.info(f"📧 Found {len(mails)} pending mails for processing")
    
    for mail in mails:
        mail_id = mail['id']
        message_id = mail['message_id']
        from_id = mail['from_id']
        keyboard = mail['keyboard']
        
        logging.info(f"🚀 Processing mail ID {mail_id} for user {from_id}")
                
        await m.update_mail(mail_id, 'status', 'run')
        
        keyboard = str(keyboard).replace(' ', '±').replace("'", '^').replace('"', '^')
        p = await asyncio.create_subprocess_shell(f'python -m fire mail start_mail --message_id={message_id} --from_id={from_id} --keyboard={keyboard}', shell=True, stdin=False, stdout=False, close_fds=False)
        
        
if __name__ == "__main__":
    # Reduced interval for better responsiveness (3 seconds instead of 10)
    schedule.every(3).seconds.do(checkMail)
    print("🚀 Mail scheduler started with 3-second intervals")
    logging.info("🚀 Mail scheduler started with 3-second intervals")

    loop = asyncio.get_event_loop()
    try:
        while True:
            loop.run_until_complete(schedule.run_pending())
            time.sleep(0.5)  # Reduced sleep time for better responsiveness
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped")
        logging.info("Scheduler stopped by user")