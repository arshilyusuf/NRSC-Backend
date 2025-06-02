from django.urls import path
from .views import ProjectListAPIView, PDFUploadView, AssignGradeAPIView

urlpatterns = [
    path('projects/', ProjectListAPIView.as_view(), name='project-list'),
    path('projects/upload/', PDFUploadView.as_view(), name='project-upload-pdf'),
    path('projects/<int:project_id>/assign_grade/', AssignGradeAPIView.as_view(), name='assign-grade'),
]