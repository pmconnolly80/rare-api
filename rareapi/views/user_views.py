import os
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rareapi.models import RareUser, DemotionQueue
from rareapi.serializers import ProfileDetailSerializer, ProfileListSerializer, ProfileUpdateSerializer, DemotionQueueSerializer
from rareapi.services import admin_actions


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_detail(request, pk):
    try:
        user = RareUser.objects.get(pk=pk)
    except RareUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    if request.method == 'GET':
        serializer = ProfileDetailSerializer(user, context={'request': request})
        return Response(serializer.data)

    if request.user.id != pk:
        return Response({'error': 'Forbidden'}, status=403)

    serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(ProfileDetailSerializer(user, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_list(request):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    users = RareUser.objects.order_by('username')
    return Response(ProfileListSerializer(users, many=True).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def deactivate_user(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    try:
        target = RareUser.objects.get(pk=pk)
    except RareUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    result = admin_actions.deactivate_user(actor=request.user, target=target)
    if result.executed:
        return Response(status=204)
    if result.queued:
        return Response({'message': result.message}, status=202)
    return Response({'error': result.message}, status=400)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reactivate_user(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    try:
        user = RareUser.objects.get(pk=pk)
    except RareUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    user.is_active = True
    user.save()
    return Response(status=204)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_user_type(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    try:
        target = RareUser.objects.get(pk=pk)
    except RareUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    result = admin_actions.change_user_role(
        actor=request.user,
        target=target,
        new_role=request.data.get('user_type'),
    )
    if result.executed:
        return Response(status=204)
    if result.queued:
        return Response({'message': result.message}, status=202)
    return Response({'error': result.message}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def demotion_queue_list(request):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    queue_items = DemotionQueue.objects.select_related('admin').all()
    return Response(DemotionQueueSerializer(queue_items, many=True).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request, pk):
    if request.user.id != pk:
        return Response({'error': 'Forbidden'}, status=403)

    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=400)

    image = request.FILES['image']
    filename = f"profile_{pk}_{image.name}"
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'profile_images')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb+') as dest:
        for chunk in image.chunks():
            dest.write(chunk)

    relative_url = f"{settings.MEDIA_URL}profile_images/{filename}"
    absolute_url = request.build_absolute_uri(relative_url)

    try:
        user = RareUser.objects.get(pk=pk)
    except RareUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    user.profile_image_url = absolute_url
    user.save()

    return Response({'profile_image_url': absolute_url})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_demotion_queue_item(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    try:
        item = DemotionQueue.objects.get(pk=pk)
    except DemotionQueue.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    if item.admin != request.user:
        return Response({'error': 'You can only cancel your own votes.'}, status=403)

    item.delete()
    return Response(status=204)
