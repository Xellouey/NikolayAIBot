import peewee
from datetime import datetime
from .core import con, orm


class SupportTicket(peewee.Model):
    """Model for support tickets"""
    
    user_id = peewee.BigIntegerField()
    subject = peewee.TextField()
    description = peewee.TextField()
    status = peewee.CharField(max_length=20, default='open')  # open, in_progress, closed
    priority = peewee.CharField(max_length=10, default='normal')  # low, normal, high, urgent
    category = peewee.CharField(max_length=50, default='general')  # general, payment, technical, etc
    assigned_admin_id = peewee.BigIntegerField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now)
    closed_at = peewee.DateTimeField(null=True)
    
    class Meta:
        database = con
        
    async def create_ticket(self, user_id, subject, description, **kwargs):
        """Create new support ticket"""
        ticket = await orm.create(SupportTicket,
                                user_id=user_id,
                                subject=subject,
                                description=description,
                                **kwargs)
        return ticket
    
    async def get_ticket(self, ticket_id):
        """Get ticket by ID"""
        try:
            # Передаем уже отфильтрованный запрос в AsyncManager.get()
            query = SupportTicket.select().where(SupportTicket.id == ticket_id)
            ticket = await orm.get(query)
            return ticket
        except Exception:
            return None
    
    async def get_user_tickets(self, user_id):
        """Get all tickets by user"""
        tickets = await orm.execute(
            SupportTicket.select()
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
            .dicts()
        )
        return list(tickets)
    
    async def get_all_tickets(self, status=None, limit=None):
        """Get all tickets for admin"""
        query = SupportTicket.select().order_by(SupportTicket.created_at.desc())
        
        if status:
            query = query.where(SupportTicket.status == status)
        
        if limit:
            query = query.limit(limit)
            
        tickets = await orm.execute(query.dicts())
        return list(tickets)
    
    async def get_tickets_count_by_status(self):
        """Get count of tickets by status"""
        all_tickets = await self.get_all_tickets()
        
        counts = {
            'open': 0,
            'in_progress': 0,
            'closed': 0,
            'total': len(all_tickets)
        }
        
        for ticket in all_tickets:
            status = ticket['status']
            if status in counts:
                counts[status] += 1
        
        return counts
    
    async def update_ticket(self, ticket_id, **kwargs):
        """Update ticket"""
        kwargs['updated_at'] = datetime.now()
        if 'status' in kwargs and kwargs['status'] == 'closed':
            kwargs['closed_at'] = datetime.now()
            
        # ВАЖНО: используем распаковку **kwargs для корректного формирования UPDATE
        await orm.execute(
            SupportTicket.update(**kwargs)
            .where(SupportTicket.id == ticket_id)
        )
    
    async def assign_ticket(self, ticket_id, admin_id):
        """Assign ticket to admin"""
        await self.update_ticket(ticket_id, 
                               assigned_admin_id=admin_id,
                               status='in_progress')
    
    async def close_ticket(self, ticket_id):
        """Close ticket"""
        await self.update_ticket(ticket_id, status='closed')


class TicketMessage(peewee.Model):
    """Model for ticket messages"""
    
    ticket_id = peewee.ForeignKeyField(SupportTicket, backref='messages')
    sender_id = peewee.BigIntegerField()
    sender_type = peewee.CharField(max_length=10)  # 'user' or 'admin'
    message_text = peewee.TextField()
    message_type = peewee.CharField(max_length=20, default='text')  # text, photo, document, etc
    file_id = peewee.TextField(null=True)  # Telegram file_id for media
    created_at = peewee.DateTimeField(default=datetime.now)
    
    class Meta:
        database = con
        
    async def create_message(self, ticket_id, sender_id, sender_type, message_text, **kwargs):
        """Create new ticket message"""
        message = await orm.create(TicketMessage,
                                 ticket_id=ticket_id,
                                 sender_id=sender_id,
                                 sender_type=sender_type,
                                 message_text=message_text,
                                 **kwargs)
        
        # Update ticket updated_at
        support_ticket = SupportTicket()
        await support_ticket.update_ticket(ticket_id, updated_at=datetime.now())
        
        return message
    
    async def get_ticket_messages(self, ticket_id):
        """Get all messages for a ticket"""
        messages = await orm.execute(
            TicketMessage.select()
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.created_at.asc())
            .dicts()
        )
        return list(messages)
    
    async def get_last_message(self, ticket_id):
        """Get last message for a ticket"""
        try:
            message = await orm.get(
                TicketMessage
                .select()
                .where(TicketMessage.ticket_id == ticket_id)
                .order_by(TicketMessage.created_at.desc())
            )
            return message
        except:
            return None