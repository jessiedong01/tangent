from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import UserProfile, Group, Event, GroupMembership, Connection, Message
import json
from datetime import datetime
from django.utils import timezone
import openai
from django.conf import settings
import math
from django.urls import reverse

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'match/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'match/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'match/register.html')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user = authenticate(request, username=username, password=password)
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'match/register.html')

@login_required
def dashboard_view(request):
    user = request.user
    profile = user.userprofile
    
    # Get user's groups
    groups = Group.objects.filter(groupmembership__profile=profile)
    
    # Get upcoming events
    events = Event.objects.filter(
        start_date__gte=timezone.now()
    ).order_by('start_date')[:5]
    
    # Get recommended connections
    recommended_connections = get_recommended_connections(profile)
    
    return render(request, 'match/dashboard.html', {
        'user': user,
        'groups': groups,
        'events': events,
        'recommended_connections': recommended_connections
    })

@login_required
def profile_view(request):
    user = request.user
    profile = user.userprofile
    
    if request.method == 'POST':
        # Update profile information
        profile.bio = request.POST.get('bio', '')
        
        # Handle interests
        interests = request.POST.get('interests', '').split(',')
        profile.interests = [interest.strip() for interest in interests if interest.strip()]
        
        # Handle current projects
        projects = request.POST.get('current_projects', '').split(',')
        profile.current_projects = [project.strip() for project in projects if project.strip()]
        
        # Handle location
        try:
            lat = float(request.POST.get('latitude', 0))
            lon = float(request.POST.get('longitude', 0))
            profile.location = {'lat': lat, 'lon': lon}
        except ValueError:
            pass
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    
    return render(request, 'match/profile.html', {'user': user})

@login_required
def groups_view(request):
    groups = Group.objects.all()
    return render(request, 'match/groups.html', {'groups': groups})

@login_required
def create_group_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        group_type = request.POST.get('group_type')
        
        # Handle location for proximity-based groups
        location = {}
        if group_type == 'PROXIMITY':
            try:
                lat = float(request.POST.get('latitude', 0))
                lon = float(request.POST.get('longitude', 0))
                radius = float(request.POST.get('radius', 1000))  # Default 1km radius
                location = {
                    'lat': lat,
                    'lon': lon,
                    'radius': radius
                }
            except ValueError:
                messages.error(request, 'Invalid location data')
                return render(request, 'match/create_group.html')
        
        group = Group.objects.create(
            name=name,
            description=description,
            group_type=group_type,
            location=location,
            created_by=request.user
        )
        
        # Add creator as admin
        GroupMembership.objects.create(
            profile=request.user.userprofile,
            group=group,
            is_admin=True
        )
        
        messages.success(request, 'Group created successfully')
        return redirect(reverse('group_matches', args=[group.id]))
    
    return render(request, 'match/create_group.html')

@login_required
def group_match_recommendations(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    user_profile = request.user.userprofile
    others = UserProfile.objects.filter(groups=group).exclude(user=request.user)
    matches = []
    for other in others:
        shared = set(user_profile.interests) & set(other.interests)
        score = len(shared)
        if score > 0:
            matches.append({
                'profile': other,
                'shared_interests': list(shared),
                'reason': f"Shared interests: {', '.join(shared)}"
            })
    matches.sort(key=lambda m: len(m['shared_interests']), reverse=True)
    return render(request, 'match/group_matches.html', {
        'group': group,
        'matches': matches[:3]
    })

@login_required
def events_view(request):
    events = Event.objects.filter(start_date__gte=timezone.now()).order_by('start_date')
    return render(request, 'match/events.html', {'events': events})

@login_required
def create_event_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Handle location
        try:
            lat = float(request.POST.get('latitude', 0))
            lon = float(request.POST.get('longitude', 0))
            location_name = request.POST.get('location_name', '')
            location = {
                'lat': lat,
                'lon': lon,
                'name': location_name
            }
        except ValueError:
            messages.error(request, 'Invalid location data')
            return render(request, 'match/create_event.html')
        
        event = Event.objects.create(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            location=location,
            created_by=request.user
        )
        
        messages.success(request, 'Event created successfully')
        return redirect('events')
    
    return render(request, 'match/create_event.html')

def get_recommended_connections(profile):
    # Get users with similar interests
    similar_users = UserProfile.objects.exclude(
        user=profile.user
    ).filter(
        interests__overlap=profile.interests
    )
    
    # Get users in the same groups
    group_members = UserProfile.objects.filter(
        groups__in=profile.groups.all()
    ).exclude(
        user=profile.user
    )
    
    # Get users in proximity
    proximity_users = []
    if profile.location and profile.location.get('lat') and profile.location.get('lon'):
        for user_profile in UserProfile.objects.exclude(user=profile.user):
            if user_profile.location and user_profile.location.get('lat') and user_profile.location.get('lon'):
                distance = calculate_distance(
                    profile.location['lat'],
                    profile.location['lon'],
                    user_profile.location['lat'],
                    user_profile.location['lon']
                )
                if distance <= 5000:  # Within 5km
                    proximity_users.append(user_profile)
    
    # Combine all potential connections
    all_users = set(list(similar_users) + list(group_members) + proximity_users)
    
    # Generate AI-powered recommendations
    recommendations = []
    for user_profile in all_users:
        # Calculate shared interests
        shared_interests = set(profile.interests) & set(user_profile.interests)
        
        # Generate conversation starters using OpenAI
        conversation_starters = generate_conversation_starters(
            profile.interests,
            user_profile.interests,
            shared_interests
        )
        
        # Calculate recommendation score
        score = calculate_recommendation_score(
            shared_interests,
            user_profile in group_members,
            user_profile in proximity_users
        )
        
        recommendations.append({
            'user': user_profile.user,
            'shared_interests': list(shared_interests),
            'conversation_starters': conversation_starters,
            'score': score
        })
    
    # Sort by score and return top 5
    return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:5]

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def generate_conversation_starters(interests1, interests2, shared_interests):
    """Generate conversation starters using OpenAI"""
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Generate 3 professional conversation starters based on these shared interests: {', '.join(shared_interests)}
        Make them engaging and specific to professional networking.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional networking assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        starters = response.choices[0].message.content.strip().split('\n')
        return [s.strip('- ') for s in starters if s.strip()]
    except Exception as e:
        print(f"Error generating conversation starters: {e}")
        return ["I noticed we share an interest in " + interest for interest in shared_interests[:3]]

def calculate_recommendation_score(shared_interests, in_same_group, in_proximity):
    """Calculate a recommendation score based on various factors"""
    score = 0
    
    # Shared interests weight
    score += len(shared_interests) * 10
    
    # Group membership weight
    if in_same_group:
        score += 20
    
    # Proximity weight
    if in_proximity:
        score += 15
    
    return score

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
