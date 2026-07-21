from typing import Annotated

from fastapi import Depends

from app.dependencies.authentication import get_auth_user
from app.modules.user import User

CurrentUser = Annotated[User, Depends(get_auth_user)]
