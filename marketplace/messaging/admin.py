from django.contrib import admin
from .models import Conversation, Message, UserBlock, UserReport


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'client', 'vendeur', 'product', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'content', 'is_read', 'created_at')


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported', 'reason', 'created_at')
    list_filter = ('reason',)
    readonly_fields = ('reporter', 'reported', 'reason', 'details', 'created_at')
