from aiogram.fsm.state import State, StatesGroup


class FSMMail(StatesGroup):
    date_mail = State()
    media = State()  # Новый этап для загрузки фото/видео
    message = State()
    keyboard = State()
    confirm = State()
    
    
class FSMAdminRights(StatesGroup):
    user = State()
    
    
class FSMEditor(StatesGroup):
    action = State()
    value = State()
    
    
class FSMCreateStep(StatesGroup):
    step = State()


class FSMLesson(StatesGroup):
    """States for lesson management"""
    title = State()
    description = State()
    price = State()
    content = State()
    preview = State()
    edit_select = State()
    edit_field = State()
    edit_value = State()
    delete_confirm = State()


class FSMPurchase(StatesGroup):
    """States for lesson purchase"""
    promocode = State()
    payment = State()


class FSMPromocode(StatesGroup):
    """States for promocode management"""
    code = State()
    discount_type = State()
    discount_value = State()
    usage_limit = State()
    expiry_date = State()


class FSMSettings(StatesGroup):
    """States for system settings"""
    currency_rate = State()
    text_edit = State()
    text_category = State()
    text_key = State()
    text_value = State()
    text_confirm = State()


class FSMSupport(StatesGroup):
    """States for support ticket system"""
    waiting_subject = State()
    waiting_description = State()
    waiting_response = State()
    admin_responding = State()


class FSMTranslations(StatesGroup):
    """States for translations management"""
    language = State()
    step = State()
    field = State()
    value = State()


class FSMLeadMagnet(StatesGroup):
    """States for lead magnet management"""
    editing_text = State()
    editing_label = State()
    
    # Content management states
    selecting_content_type = State()
    uploading_video = State()
    uploading_photo = State()
    uploading_document = State()


# class FSMSuperPower(StatesGroup):
    # birthdate = State()
