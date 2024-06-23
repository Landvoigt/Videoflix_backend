# from rest_framework import status
# from rest_framework.authtoken.views import Response, APIView
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated

# from .models import Profile
# from .serializers import ProfileSerializer


# class ProfileViewSet(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, pk=None, format=None):
#         if pk:
#             try:
#                 profile = Profile.objects.get(pk=pk, user=request.user)
#                 serializer = ProfileSerializer(profile)
#                 return Response(serializer.data)
#             except Profile.DoesNotExist:
#                 return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
#         else:
#             profiles = Profile.objects.filter(user=request.user)
#             serializer = ProfileSerializer(profiles, many=True)
#             return Response(serializer.data)
    
#     def post(self, request, format=None):
#         serializer = ProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk=None, format=None):
#         try:
#             profile = Profile.objects.get(pk=pk, user=request.user)
#         except Profile.DoesNotExist:
#             return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

#         serializer = ProfileSerializer(profile, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#     def delete(self, request, pk=None, format=None):
#         try:
#             profile = Profile.objects.get(pk=pk, user=request.user)
#         except Profile.DoesNotExist:
#             return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

#         profile.delete()
#         return Response({'success': 'Profile deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Profile
from .serializers import ProfileSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': 'Profile deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()