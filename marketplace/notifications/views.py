from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    # Marquer toutes comme lues à l'ouverture de la page
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })


@login_required
def mark_read_and_redirect(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.url:
        return redirect(notif.url)
    return redirect('notification_list')
