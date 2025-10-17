"""
View functions for the news application.

This module contains all the view functions that handle HTTP requests
and responses for the news portal application, including authentication,
article management, and publisher operations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils import timezone
from .models import Article, Newsletter, Publisher, CustomUser
from .forms import CustomUserCreationForm, ArticleForm, NewsletterForm
from .twitter_utils import send_tweet


def home(request):
    """
    Display the home page with latest approved articles.
    
    Shows the 10 most recent approved articles to all visitors,
    regardless of authentication status.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered home page with articles context
    """
    articles = Article.objects.filter(is_approved=True).order_by('-created_at')[:10]
    return render(request, 'news_app/home.html', {'articles': articles})


def register_view(request):
    """
    Handle user registration with role-based account creation.
    
    Processes registration form submissions and creates new user accounts
    with the specified role (reader, journalist, or editor).
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Registration form or redirect to home on success
    """
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        role = request.POST['role']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, 'news_app/register.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'news_app/register.html')
        
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password1,
                role=role
            )
            
            group, created = Group.objects.get_or_create(name=role.capitalize())
            user.groups.add(group)
            
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {username}!")
            return redirect('home')
        
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'news_app/register.html')
        
    return render(request, 'news_app/register.html')


def login_view(request):
    """
    Handle user authentication and login.
    
    Authenticates users against the database and logs them in
    upon successful credential verification.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Login form or redirect to home on success
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'news_app/login.html')


def logout_view(request):
    """
    Handle user logout.
    
    Logs out the currently authenticated user and redirects to home page.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Redirect to home page
    """
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')


@login_required
def dashboard(request):
    """
    Display role-specific dashboard for authenticated users.
    
    Provides customized dashboard views based on user role:
    - Readers: See content from their subscriptions
    - Journalists: Manage their articles and newsletters
    - Editors: Review pending articles and manage publishers
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Role-specific dashboard template with context
    """
    user = request.user
    
    if user.role == 'reader':
        subscribed_publishers = user.subscribed_publishers.all()
        subscribed_journalists = user.subscribed_journalists.all()
        
        articles = Article.objects.filter(
            is_approved=True
        ).filter(
            Q(publisher__in=subscribed_publishers) |
            Q(journalist__in=subscribed_journalists)
        ).order_by('-created_at')[:10]
        
        newsletters = Newsletter.objects.filter(
            is_published=True
        ).filter(
            Q(publisher__in=subscribed_publishers) |
            Q(created_by__in=subscribed_journalists)
        ).order_by('-created_at')[:10]
        
        context = {
            'articles': articles,
            'newsletters': newsletters,
            'subscribed_publishers': subscribed_publishers,
            'subscribed_journalists': subscribed_journalists,
        }
        
    elif user.role == 'journalist':
        my_articles = Article.objects.filter(journalist=user).order_by('-created_at')
        my_newsletters = Newsletter.objects.filter(created_by=user).order_by('-created_at')
        publishers = Publisher.objects.all()
        
        context = {
            'my_articles': my_articles,
            'my_newsletters': my_newsletters,
            'publishers': publishers,
        }
        
    elif user.role == 'editor':
        user_publishers = Publisher.objects.filter(Q(owner=user) | Q(editors=user)).distinct()
        journalist_ids = CustomUser.objects.filter(
            Q(associated_publishers__in=user_publishers) | 
            Q(authored_articles__publisher__in=user_publishers)
        ).distinct().values_list('id', flat=True)
        
        pending_articles = Article.objects.filter(
            is_approved=False,
            journalist_id__in=journalist_ids
        ).order_by('-created_at')
        
        all_articles = Article.objects.filter(
            journalist_id__in=journalist_ids
        ).order_by('-created_at')[:10]
        
        context = {
            'pending_articles': pending_articles,
            'all_articles': all_articles,
            'user_publishers': user_publishers,
        }
        
    return render(request, f'news_app/dashboard_{user.role}.html', context)


@login_required
def create_article(request):
    """
    Handle article creation by journalists.
    
    Allows journalists to create new articles. Articles associated with
    publishers require editorial approval before publication.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Article creation form or redirect to dashboard
    """
    if request.user.role != 'journalist':
        messages.error(request, "Only journalists can create articles.")
        return redirect('dashboard')
    
    user_publishers = request.user.associated_publishers.all()
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, user_publishers=user_publishers)
        if form.is_valid():
            article = form.save(commit=False)
            article.journalist = request.user
            if article.publisher:
                article.is_approved = False
                messages.success(request, "Article created and submitted for publisher approval.")
            else:
                article.is_approved = True
                messages.success(request, "Independent article published successfully.")
                
            article.save()
            return redirect('dashboard')
    else:
        form = ArticleForm(user_publishers=user_publishers)
        
    return render(request, 'news_app/create_article.html', {'form': form})


@login_required
def edit_article(request, article_id):
    """
    Handle article editing by journalists and editors.
    
    Allows the original journalist or editors to modify existing articles.
    
    Args:
        request: HTTP request object
        article_id (int): ID of the article to edit
        
    Returns:
        HttpResponse: Article editing form or redirect to dashboard
    """
    article = get_object_or_404(Article, id=article_id)
    
    if request.user != article.journalist and request.user.role != 'editor':
        messages.error(request, "You don't have permission to edit this article.")
        return redirect('dashboard')
    
    user_publishers = request.user.associated_publishers.all()
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article, user_publishers=user_publishers)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully!")
            return redirect('dashboard')
    else:
        form = ArticleForm(instance=article, user_publishers=user_publishers)
            
    return render(request, 'news_app/edit_article.html', {'form': form, 'article': article})


@login_required
def delete_article(request, article_id):
    """
    Handle article deletion by journalists and editors.
    
    Allows the original journalist or editors to delete articles.
    
    Args:
        request: HTTP request object
        article_id (int): ID of the article to delete
        
    Returns:
        HttpResponse: Delete confirmation page or redirect to dashboard
    """
    article = get_object_or_404(Article, id=article_id)
    
    if request.user != article.journalist and request.user.role != 'editor':
        messages.error(request, "You don't have permission to delete this article.")
        return redirect('dashboard')
    
    if request.method == "POST":
        article_title = article.title
        article.delete()
        messages.success(request, f"Article '{article_title}' deleted successfully!")
        return redirect('dashboard')
    
    return render(request, 'news_app/delete_article.html', {'article': article})


@login_required
def create_newsletter(request):
    """
    Handle newsletter creation by journalists.
    
    Allows journalists to create newsletters that can be sent to subscribers.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Newsletter creation form or redirect to dashboard
    """
    if request.user.role != 'journalist':
        messages.error(request, "Only journalists can create newsletters.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.created_by = request.user
            newsletter.save()
            messages.success(request, "Newsletter created successfully!")
            return redirect('dashboard')
    else:
        form = NewsletterForm()
    
    return render(request, 'news_app/create_newsletter.html', {'form': form})


@login_required
def edit_newsletter(request, newsletter_id):
    """
    Handle newsletter editing by journalists and editors.
    
    Allows the creator or editors to modify existing newsletters.
    
    Args:
        request: HTTP request object
        newsletter_id (int): ID of the newsletter to edit
        
    Returns:
        HttpResponse: Newsletter editing form or redirect to dashboard
    """
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.user != newsletter.created_by and request.user.role != 'editor':
        messages.error(request, "You don't have permission to edit this newsletter.")
        return redirect('dashboard')
    
    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, "Newsletter updated successfully!")
            return redirect('dashboard')
    else:
        form = NewsletterForm(instance=newsletter)
        
    return render(request, 'news_app/edit_newsletter.html', {'form': form, 'newsletter': newsletter})


@login_required
def delete_newsletter(request, newsletter_id):
    """
    Handle newsletter deletion by journalists and editors.
    
    Allows the creator or editors to delete newsletters.
    
    Args:
        request: HTTP request object
        newsletter_id (int): ID of the newsletter to delete
        
    Returns:
        HttpResponse: Delete confirmation page or redirect to dashboard
    """
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.user != newsletter.created_by and request.user.role != 'editor':
        messages.error(request, "You don't have permission to delete this newsletter.")
        return redirect('dashboard')

    if request.method == 'POST':
        newsletter_title = newsletter.title
        newsletter.delete()
        messages.success(request, f"Newsletter '{newsletter_title}' deleted successfully!")
        return redirect('dashboard')
    
    return render(request, 'news_app/delete_newsletter.html', {'newsletter': newsletter})


@login_required
def approve_article(request, article_id):
    """
    Handle article approval by editors.
    
    Allows editors to approve articles from their publishing houses
    and automatically shares approved articles on Twitter.
    
    Args:
        request: HTTP request object
        article_id (int): ID of the article to approve
        
    Returns:
        HttpResponse: Approval confirmation page or redirect to dashboard
    """
    if request.user.role != 'editor':
        messages.error(request, "You don't have permission to approve articles.")
        return redirect('dashboard')
    
    article = get_object_or_404(Article, id=article_id)
    
    user_publishers = Publisher.objects.filter(Q(owner=request.user) | Q(editors=request.user)).distinct()
    
    if (article.publisher and 
        request.user not in article.publisher.editors.all() and 
        request.user != article.publisher.owner and
        article.publisher not in user_publishers):
        messages.error(request, "You can only approve articles from your publishing house.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        article.is_approved = True
        article.approved_by = request.user
        article.approved_at = timezone.now()
        article.save()
        
        if send_tweet(article):
            messages.success(request, f"Article '{article.title}' approved and tweeted!")
        else:
            messages.warning(request, f"Article '{article.title}' approved but tweet failed to send.")

        return redirect('dashboard')
    
    return render(request, 'news_app/approve_article.html', {'article': article})


@login_required
def manage_subscriptions(request):
    """
    Handle subscription management for readers.
    
    Allows readers to subscribe/unsubscribe from publishers and journalists.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Subscription management form or redirect to dashboard
    """
    if request.user.role != 'reader':
        messages.error(request, "Only readers can manage subscriptions.")
        return redirect('dashboard')
    
    publishers = Publisher.objects.all()
    journalists = CustomUser.objects.filter(role='journalist')
    
    if request.method == 'POST':
        subscribed_publishers = request.POST.getlist('publishers')
        subscribed_journalists = request.POST.getlist('journalists')
        
        request.user.subscribed_publishers.set(subscribed_publishers)
        request.user.subscribed_journalists.set(subscribed_journalists)
        
        messages.success(request, "Subscriptions updated!")
        return redirect('dashboard')
    
    context = {
        'publishers': publishers,
        'journalists': journalists,
        'current_publishers': request.user.subscribed_publishers.all(),
        'current_journalists': request.user.subscribed_journalists.all(),
    }
    
    return render(request, 'news_app/manage_subscriptions.html', context)


@login_required
def article_detail(request, article_id):
    """
    Display individual article details.
    
    Shows full article content with access control for unapproved articles.
    
    Args:
        request: HTTP request object
        article_id (int): ID of the article to display
        
    Returns:
        HttpResponse: Article detail page or redirect if no permission
    """
    article = get_object_or_404(Article, id=article_id)
    
    if not article.is_approved and request.user not in [article.journalist, article.approved_by]:
        messages.error(request, "You don't have permission to view this article.")
        return redirect('dashboard')
    
    return render(request, 'news_app/article_detail.html', {'article': article})


@login_required
def register_publisher(request):
    """
    Handle new publisher registration by editors.
    
    Allows editors to register new publishing houses they will own.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Publisher registration form or redirect to dashboard
    """
    if request.user.role != 'editor':
        messages.error(request, "Only editors can register publishing houses.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        
        publisher = Publisher.objects.create(
            name=name,
            description=description,
            owner=request.user
        )
        publisher.editors.add(request.user)
        messages.success(request, f"Publishing house '{name}' created successfully!")
        return redirect('dashboard')
    
    return render(request, 'news_app/register_publisher.html')


@login_required
def join_publisher(request, publisher_id):
    """
    Handle users joining existing publishing houses.
    
    Allows editors and journalists to join publishing houses as members.
    
    Args:
        request: HTTP request object
        publisher_id (int): ID of the publisher to join
        
    Returns:
        HttpResponse: Join confirmation page or redirect to dashboard
    """
    if request.user.role not in ['editor', 'journalist']:
        messages.error(request, "Only editors and journalists can join publishing houses.")
        return redirect('dashboard')
    
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    if request.method == 'POST':
        if request.user.role == 'editor':
            publisher.editors.add(request.user)
            messages.success(request, f"You have joined {publisher.name} as an editor.")
        elif request.user.role == 'journalist':
            publisher.journalists.add(request.user)
            messages.success(request, f"You have joined {publisher.name} as a journalist.")
            
        return redirect('dashboard')
    
    return render(request, 'news_app/join_publisher.html', {'publisher': publisher})


@login_required
def list_publishers(request):
    """
    Display list of all publishing houses.
    
    Shows all registered publishing houses in the system.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Publishers listing page
    """
    publishers = Publisher.objects.all()
    return render(request, 'news_app/list_publishers.html', {'publishers': publishers})


@login_required
def manage_publisher(request, publisher_id):
    """
    Handle publisher management by owners and editors.
    
    Allows publisher owners and editors to manage their publishing house,
    including adding/removing staff and reviewing pending articles.
    
    Args:
        request: HTTP request object
        publisher_id (int): ID of the publisher to manage
        
    Returns:
        HttpResponse: Publisher management dashboard
    """
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    if request.user != publisher.owner and request.user not in publisher.editors.all():
        messages.error(request, "You don't have permission to manage this publishing house.")
        return redirect('dashboard')
    
    current_editors = publisher.editors.all()
    current_journalists = publisher.journalists.all()
    
    available_editors = CustomUser.objects.filter(role='editor').exclude(id__in=current_editors.values_list('id', flat=True))
    available_journalists = CustomUser.objects.filter(role='journalist').exclude(id__in=current_journalists.values_list('id', flat=True))
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_editor':
            editor_username = request.POST.get('editor_username')
            try:
                editor = CustomUser.objects.get(username=editor_username, role='editor')
                publisher.editors.add(editor)
                messages.success(request, f"Editor {editor_username} added to publishing house.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Editor not found.")
        
        elif action == 'remove_editor':
            editor_id = request.POST.get('editor_id')
            try:
                editor = CustomUser.objects.get(id=editor_id, role='editor')
                publisher.editors.remove(editor)
                messages.success(request, f"Editor {editor.username} removed from publishing house.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Editor not found.")
        
        elif action == 'add_journalist':
            journalist_username = request.POST.get('journalist_username')
            try:
                journalist = CustomUser.objects.get(username=journalist_username, role='journalist')
                publisher.journalists.add(journalist)
                messages.success(request, f"Journalist {journalist_username} added to publishing house.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Journalist not found.")
        
        elif action == 'remove_journalist':
            journalist_id = request.POST.get('journalist_id')
            try:
                journalist = CustomUser.objects.get(id=journalist_id, role='journalist')
                publisher.journalists.remove(journalist)
                messages.success(request, f"Journalist {journalist.username} removed from publishing house.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Journalist not found.")
    
    pending_articles = Article.objects.filter(
        publisher=publisher,
        is_approved=False
    ).order_by('-created_at')
    
    context = {
        'publisher': publisher,
        'pending_articles': pending_articles,
        'available_editors': available_editors,
        'available_journalists': available_journalists,
    }
    
    return render(request, 'news_app/manage_publisher.html', context)
        
        

