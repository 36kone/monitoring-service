from fastapi import HTTPException, status


def ensure_or_400[T](obj: T | None, message: str = "Recurso inválido ou inexistente") -> T:
    if not obj:
        raise HTTPException(status_code=400, detail=message)
    return obj


def ensure_400[T](obj: T | None, message: str = "Recurso inválido ou inexistente") -> T:
    """

    :rtype: T
    """
    if obj:
        raise HTTPException(status_code=400, detail=message)
    return obj


def ensure_or_401[T](obj: T | None, message: str = "Recurso inválido ou inexistente") -> T:
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return obj


def ensure_or_404[T](obj: T | None, message: str = "Recurso não encontrado") -> T:
    if not obj:
        raise HTTPException(status_code=404, detail=message)
    return obj


def ensure_or_400_json[T](obj: T | None, message: dict = "Recurso inválido ou inexistente") -> T:
    if not obj:
        raise HTTPException(status_code=400, detail=message)
    return obj


def ensure_list_or_404(obj: list, message: str = "Not found"):
    if not obj:
        raise HTTPException(status_code=404, detail=message)
    return obj


def ensure_list_or_400(obj: list, message: str = "Recurso inválido ou inexistente"):
    if not obj:
        raise HTTPException(status_code=400, detail=message)
    return obj


def ensure_or_403[T](obj: T | None, message: str = "Acesso negado") -> T:
    if not obj:
        raise HTTPException(status_code=403, detail=message)
    return obj


def ensure_403[T](obj: T, message: str = "Acesso negado") -> T:
    if obj:
        raise HTTPException(status_code=403, detail=message)
    return obj


def assert_or_400(condition: bool, message: str = "Dados inválidos"):
    if not condition:
        raise HTTPException(status_code=400, detail=message)


def assert_or_403(condition: bool, message: str = "Ação não permitida"):
    if not condition:
        raise HTTPException(status_code=403, detail=message)


def assert_or_422(condition: bool, message: str = "Dados inválidos ou incompletos"):
    if not condition:
        raise HTTPException(status_code=422, detail=message)


def require[T](value: T | None, message: str = "Campo obrigatório") -> T:
    if not value:
        raise HTTPException(status_code=422, detail=message)
    return value
