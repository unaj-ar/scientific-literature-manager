import pytest
from unittest.mock import MagicMock
from services.user_service import UserService
from fastapi import HTTPException


def test_deactivate_user_success():
    mock_repo = MagicMock()
    mock_repo.soft_delete.return_value = True

    service = UserService(user_repository=mock_repo)
    response = service.deactivate_user(user_id=2, current_user_id=1)

    assert response["message"] == "Usuario 2 dado de baja exitosamente."
    mock_repo.soft_delete.assert_called_once_with(2)


def test_deactivate_self_user_raises_error():
    mock_repo = MagicMock()
    service = UserService(user_repository=mock_repo)

    with pytest.raises(HTTPException) as exc_info:
        service.deactivate_user(user_id=1, current_user_id=1)

    assert exc_info.value.status_code == 400