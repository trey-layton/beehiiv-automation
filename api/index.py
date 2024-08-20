from mangum import Mangum
from .main import api_app

handler = Mangum(api_app)
