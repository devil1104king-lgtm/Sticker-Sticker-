from telegram.ext import filters
from config import Config

class AdminFilter(filters.BaseFilter):
    """Filter that allows only the owner."""

    def __init__(self):
        self.owner_id = Config.OWNER_ID

    async def __call__(self, update, context):
        user = update.effective_user
        return user and user.id == self.owner_id

admin_filter = AdminFilter()
