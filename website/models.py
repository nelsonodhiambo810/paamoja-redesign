from django.db import models

class Program(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='programs/', blank=True, null=True)
    
    def __str__(self):
        return self.title

class NewsUpdate(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    link = models.URLField(blank=True)
    
    def __str__(self):
        return self.title

class SuccessStory(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100) # e.g. "DIYEP Graduate"
    quote = models.TextField()
    photo = models.ImageField(upload_to='stories/', blank=True)
    
    def __str__(self):
        return self.name