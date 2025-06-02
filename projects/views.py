import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import serializers, status
from django.conf import settings
from . import counter  # For counting PDF uploads
from .new_pdf import process_new_pdf  # ✅ Import the processing function

class ProjectListAPIView(APIView):
    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR, 'parsed_data.json')
        try:
            with open(file_path, 'r') as f:
                projects = json.load(f)
            return Response(projects)
        except FileNotFoundError:
            return Response({"error": "JSON file not found"}, status=404)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format"}, status=500)

# Serializer to validate PDF uploads
class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return value

# PDF upload view
class PDFUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PDFUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']

            # Set upload directory
            upload_dir = os.path.join(settings.BASE_DIR, 'pdf_folder')
            os.makedirs(upload_dir, exist_ok=True)

            # Get the next available number from the counter
            next_number = counter.get_next_count()

            # Generate the new filename
            new_filename = f'project_report ({next_number}).pdf'
            file_path = os.path.join(upload_dir, new_filename)

            # Save the uploaded PDF file
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # ✅ Trigger Gemini processing
            process_new_pdf(file_path)

            return Response({
                "message": "PDF uploaded and processed successfully",
                "file_url": request.build_absolute_uri('/pdf_folder/' + new_filename)
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Serializer for assigning grades
class GradeAssignmentSerializer(serializers.Serializer):
    grade = serializers.IntegerField(min_value=0, max_value=100)

class AssignGradeAPIView(APIView):
    def post(self, request, project_id):
        serializer = GradeAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            grade = serializer.validated_data['grade']
            file_path = os.path.join(settings.BASE_DIR, 'parsed_data.json')
            try:
                with open(file_path, 'r+') as f:
                    projects = json.load(f)
                    for project in projects:
                        if project.get('project_id') == int(project_id):
                            project['grade'] = grade
                            f.seek(0)
                            json.dump(projects, f, indent=4)
                            f.truncate()
                            return Response({"message": f"Grade assigned successfully to project {project_id}"}, status=status.HTTP_200_OK)
                    return Response({"error": f"Project with id {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except FileNotFoundError:
                return Response({"error": "JSON file not found"}, status=status.HTTP_404_NOT_FOUND)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
