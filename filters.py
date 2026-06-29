from telegram.ext import filters
from config import Config

# Filter to isolate commands originating from Admins only
AdminFilter = filters.User(Config.ADMINS)
