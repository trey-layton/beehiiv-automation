from mangum import Mangum
from api.main import api_app

handler = Mangum(api_app)
