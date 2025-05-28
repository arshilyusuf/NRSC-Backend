from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os

class ProjectListAPIView(APIView):
    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR, 'parsed_data.txt')
        projects = parse_projects_from_file(file_path)
        return Response(projects)


def parse_projects_from_file(filepath):
    projects = []
    if not os.path.exists(filepath):
        return projects

    with open(filepath, 'r') as f:
        content = f.read()

    raw_projects = content.strip().split('---')

    for raw_project in raw_projects:
        project_data = {}
        for line in raw_project.strip().split('\n'):
            if ': ' in line:
                key, value = line.split(': ', 1)
                project_data[key.strip()] = value.strip()
        if project_data:
            projects.append(project_data)

    return projects