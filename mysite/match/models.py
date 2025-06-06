from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Create your models here.

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.JSONField(default=dict)  # {lat: float, lon: float, name: str}
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Group(models.Model):
    GROUP_TYPES = [
        ('PROXIMITY', 'Proximity-based'),
        ('EVENT', 'Event-based'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    location = models.JSONField(default=dict)  # {lat: float, lon: float, radius: float}
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    interests = models.JSONField(default=list)
    current_projects = models.JSONField(default=list)
    location = models.JSONField(default=dict)  # {lat: float, lon: float}
    groups = models.ManyToManyField(Group, through='GroupMembership')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    last_location_update = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class GroupMembership(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('profile', 'group')

class Connection(models.Model):
    user1 = models.ForeignKey(User, related_name='connections1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='connections2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    shared_interests = models.JSONField(default=list)
    conversation_starters = models.JSONField(default=list)
    
    class Meta:
        unique_together = ('user1', 'user2')

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
