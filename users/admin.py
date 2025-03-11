from django.contrib import admin
from .models import Profile, Record, Techsupport, AccountInfo

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number')

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'department', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('name', 'address')

@admin.register(Techsupport)
class TechsupportAdmin(admin.ModelAdmin):
    list_display = ('user', 'support_type', 'status', 'created_at')
    list_filter = ('support_type', 'status', 'created_at')
    search_fields = ('user__username', 'description')

@admin.register(AccountInfo)
class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ("id","username", "account_balance", "contact_details", "last_transactions")
    search_fields = ("username", "contact_details")
    readonly_fields = ("last_transactions",)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:  # Editing an existing object
            return ['username', 'account_balance', 'contact_details', 'last_transactions']
        return ['username', 'account_balance', 'contact_details']
