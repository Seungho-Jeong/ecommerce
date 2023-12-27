from rest_framework import generics


class AccountRegisterView(generics.CreateAPIView):
    serializer_class = AccountRegisterSerializer
    permission_classes = (AllowAny,)