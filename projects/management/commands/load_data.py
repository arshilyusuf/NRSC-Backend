from django.core.management.base import BaseCommand
from projects.models import Project

class Command(BaseCommand):
    help = 'Load project data from parsed_data.txt'

    def handle(self, *args, **kwargs):
        with open('parsed_data.txt', 'r') as f:
            content = f.read()

        projects = content.strip().split('---')
        for project_text in projects:
            lines = project_text.strip().split('\n')
            data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
            if data:
                Project.objects.create(**data)

        self.stdout.write(self.style.SUCCESS("Projects loaded successfully!"))
