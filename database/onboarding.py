import peewee
from datetime import datetime
from .core import con

class OnboardingStep(peewee.Model):
    key = peewee.CharField(max_length=50, unique=True)
    order = peewee.IntegerField(default=0)
    type = peewee.CharField(max_length=20, default='screen')  # screen, single_choice, multi_choice, consent
    text_key = peewee.CharField(max_length=100, null=True)
    enabled = peewee.BooleanField(default=True)
    required = peewee.BooleanField(default=True)
    metadata = peewee.TextField(null=True)  # reserved for future JSON settings
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = con
        table_name = 'onboarding_step'

class OnboardingOption(peewee.Model):
    step = peewee.ForeignKeyField(OnboardingStep, backref='options', on_delete='CASCADE')
    value = peewee.CharField(max_length=50)
    text_key = peewee.CharField(max_length=100)
    order = peewee.IntegerField(default=0)
    enabled = peewee.BooleanField(default=True)

    class Meta:
        database = con
        table_name = 'onboarding_option'
        indexes = (
            (("step", "value"), True),
        )

class OnboardingEvent(peewee.Model):
    user_id = peewee.BigIntegerField()
    step = peewee.ForeignKeyField(OnboardingStep, backref='events', on_delete='CASCADE')
    option_value = peewee.CharField(max_length=50, null=True)
    payload = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = con
        table_name = 'onboarding_event'


def ensure_default_flow():
    """Create default onboarding steps and options if none exist."""
    con.create_tables([OnboardingStep, OnboardingOption, OnboardingEvent], safe=True)

    if OnboardingStep.select().count() > 0:
        return

    # 1) welcome (screen)
    s1 = OnboardingStep.create(
        key='welcome', order=1, type='screen', text_key='onboarding.welcome', enabled=True, required=False
    )
    # 2) goal (single_choice)
    s2 = OnboardingStep.create(
        key='goal', order=2, type='single_choice', text_key='onboarding.goal.title', enabled=True, required=True
    )
    OnboardingOption.create(step=s2, value='quick_start', text_key='onboarding.goal.option.quick_start', order=1)
    OnboardingOption.create(step=s2, value='paid_course', text_key='onboarding.goal.option.paid_course', order=2)
    OnboardingOption.create(step=s2, value='support', text_key='onboarding.goal.option.support', order=3)

    # 3) level (single_choice)
    s3 = OnboardingStep.create(
        key='level', order=3, type='single_choice', text_key='onboarding.level.title', enabled=True, required=True
    )
    OnboardingOption.create(step=s3, value='beginner', text_key='onboarding.level.option.beginner', order=1)
    OnboardingOption.create(step=s3, value='intermediate', text_key='onboarding.level.option.intermediate', order=2)
    OnboardingOption.create(step=s3, value='advanced', text_key='onboarding.level.option.advanced', order=3)

    # 4) consent (single_choice)
    s4 = OnboardingStep.create(
        key='consent', order=4, type='single_choice', text_key='onboarding.consent.title', enabled=True, required=False
    )
    OnboardingOption.create(step=s4, value='yes', text_key='onboarding.consent.option.yes', order=1)
    OnboardingOption.create(step=s4, value='no', text_key='onboarding.consent.option.no', order=2)

    # 5) finish (screen)
    OnboardingStep.create(
        key='finish', order=5, type='screen', text_key='onboarding.finish', enabled=True, required=False
    )
