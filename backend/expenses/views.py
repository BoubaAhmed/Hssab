
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, Member
from .serializers import GroupSerializer


class MyGroupsMixin:
    """Only groups the current user belongs to. Anyone else gets a 404."""

    def get_queryset(self):
        return (
            Group.objects.filter(members__user=self.request.user)
            .distinct()
            .prefetch_related('members')
        )


class GroupListCreateView(MyGroupsMixin, generics.ListCreateAPIView):
    serializer_class = GroupSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        group = serializer.save()
        Member.objects.create(
            group=group,
            user=self.request.user,
            display_name=self.request.user.username,
        )


class GroupDetailView(MyGroupsMixin, generics.RetrieveAPIView):
    serializer_class = GroupSerializer


class JoinGroupView(APIView):
    @transaction.atomic
    def post(self, request, code):
        group = get_object_or_404(Group, invite_code=code)
        name = request.data.get('display_name') or request.user.username
        _, created = Member.objects.get_or_create(
            group=group, user=request.user, defaults={'display_name': name}
        )
        data = GroupSerializer(group).data
        return Response(data, status=201 if created else 200)