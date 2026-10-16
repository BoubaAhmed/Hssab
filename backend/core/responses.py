from rest_framework import status
from rest_framework.response import Response


def message_response(message: str, *, status_code: int = status.HTTP_200_OK, **extra) -> Response:
    """Réponse de succès pour une action sans ressource à renvoyer : {"message": "..."}."""
    return Response({'message': message, **extra}, status=status_code)