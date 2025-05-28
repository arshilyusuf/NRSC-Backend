from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    abstract = models.TextField()

    def __str__(self):
        return self.title
