from django.contrib import admin

from .models import Expense, ExpenseShare, Group, Member, Settlement

admin.site.register([Group, Member, Expense, ExpenseShare, Settlement])