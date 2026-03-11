from django.shortcuts import render
from .models import Program, NewsUpdate, SuccessStory # <--- Import it

def home(request):
    programs = Program.objects.all()
    news = NewsUpdate.objects.order_by('-date')[:3]
    stories = SuccessStory.objects.all() # <--- Fetch the stories
    
    return render(request, 'home.html', {
        'programs': programs,
        'news': news,
        'stories': stories # <--- Send them to the template
    })