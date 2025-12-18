from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.shortcuts import get_object_or_404

from .models import Manhwa
from .serializers import (
    ManhwaSerializer, 
    ManhwaListSerializer, 
    ManhwaCreateSerializer,
    ManhwaUpdateSerializer
)


class ManhwaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD Manhwa
    
    Endpoints:
    - GET /api/manhwa/ - List all manhwa
    - POST /api/manhwa/ - Create new manhwa
    - GET /api/manhwa/{id}/ - Detail manhwa
    - PUT /api/manhwa/{id}/ - Update manhwa (full)
    - PATCH /api/manhwa/{id}/ - Update manhwa (partial)
    - DELETE /api/manhwa/{id}/ - Delete manhwa
    - GET /api/manhwa/pending/ - List manhwa with status pending
    - GET /api/manhwa/completed/ - List manhwa with status completed
    - GET /api/manhwa/failed/ - List manhwa with status failed
    """
    queryset = Manhwa.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """
        Return serializer class sesuai action
        """
        if self.action == 'list':
            return ManhwaListSerializer
        elif self.action == 'create':
            return ManhwaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ManhwaUpdateSerializer
        return ManhwaSerializer
    
    def list(self, request, *args, **kwargs):
        """
        GET /api/manhwa/
        List all manhwa (without content field for performance)
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        """
        POST /api/manhwa/
        Create new manhwa
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Gunakan ManhwaSerializer untuk response lengkap
        response_serializer = ManhwaSerializer(serializer.instance)
        return Response({
            'success': True,
            'message': 'Manhwa berhasil dibuat',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/manhwa/{id}/
        Detail specific manhwa
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """
        PUT /api/manhwa/{id}/
        Update specific manhwa (full update)
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Gunakan ManhwaSerializer untuk response lengkap
        response_serializer = ManhwaSerializer(serializer.instance)
        return Response({
            'success': True,
            'message': 'Manhwa berhasil diupdate',
            'data': response_serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/manhwa/{id}/
        Update specific manhwa (partial update)
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/manhwa/{id}/
        Delete specific manhwa
        """
        instance = self.get_object()
        manhwa_title = instance.title
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': f'Manhwa "{manhwa_title}" berhasil dihapus'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """
        GET /api/manhwa/pending/
        List specific manhwa with status pending
        """
        queryset = self.get_queryset().filter(download_status='pending')
        serializer = ManhwaListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'], url_path='completed')
    def completed(self, request):
        """
        GET /api/manhwa/completed/
        List specific manhwa with status completed
        """
        queryset = self.get_queryset().filter(download_status='completed')
        serializer = ManhwaListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'], url_path='failed')
    def failed(self, request):
        """
        GET /api/manhwa/failed/
        List specific manhwa with status failed
        """
        queryset = self.get_queryset().filter(download_status='failed')
        serializer = ManhwaListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
