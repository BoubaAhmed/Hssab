from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from core.responses import message_response
from core.throttling import (
    EmailVerificationThrottle,
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
)

from . import services
from .serializers import (
    ChangePasswordSerializer,
    ConfirmTokenSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


class PublicAPIView(APIView):
    """Routes ouvertes : aucune authentification, donc un vieux jeton ne les bloque jamais."""

    authentication_classes = []
    permission_classes = [AllowAny]


# --- Connexion ---------------------------------------------------------------


class RegisterView(PublicAPIView):
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(**serializer.validated_data)
        body = {'user': UserSerializer(user).data, **services.issue_tokens(user)}
        return Response(body, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Connexion par email. Limitée à 10 essais par minute et par adresse IP."""

    serializer_class = LoginSerializer
    throttle_classes = [LoginThrottle]


class LogoutView(PublicAPIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.logout(refresh_token=serializer.validated_data['refresh'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Profil ------------------------------------------------------------------


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.update_profile(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tokens = services.change_password(user=request.user, **serializer.validated_data)
        return Response(tokens)


# --- Mot de passe oublié -----------------------------------------------------


class PasswordResetRequestView(PublicAPIView):
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(email=serializer.validated_data['email'])
        return message_response(
            'Si un compte existe avec cette adresse, un email vient d’être envoyé.',
            status_code=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(PublicAPIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(
            raw_token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )
        return message_response('Mot de passe modifié. Vous pouvez vous connecter.')


# --- Vérification de l'email -------------------------------------------------


class EmailVerificationRequestView(APIView):
    throttle_classes = [EmailVerificationThrottle]

    def post(self, request):
        services.request_email_verification(user=request.user)
        return message_response(
            'Un email de confirmation vient d’être envoyé.', status_code=status.HTTP_202_ACCEPTED
        )


class EmailVerificationConfirmView(PublicAPIView):
    def post(self, request):
        serializer = ConfirmTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_email_verification(raw_token=serializer.validated_data['token'])
        return message_response('Adresse email confirmée.', email_verified=True)