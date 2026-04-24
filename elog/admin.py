from django.contrib import admin

# Register your models here.
from .models import BoardType, Board, Location, TerraGreen, Log, BoardStatus, Tests, TestResult

#admin.site.register(BoardType)
#admin.site.register(Board)
#admin.site.register(Location)
#admin.site.register(Log)
admin.site.register(BoardStatus)

class BoardInline(admin.TabularInline):
  model = Board
  extra = 0

class LogInline(admin.TabularInline):
  model = Log
  extra = 0

class TestsInline(admin.TabularInline):
  model = Tests
  extra = 0

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
  list_display = ('board_type', 'board_id', 'location', 'terragreen', 'r455_replaced')
  list_filter = ('board_type', 'location', 'terragreen', 'r455_replaced')
  inlines = [LogInline]

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
  list_display = ('id', 'board', 'date', 'text')
  list_filter = ('board', 'date')

@admin.register(BoardType)
class BoardTypeAdmin(admin.ModelAdmin):
  list_display = ('name', 'description')
  inlines = [BoardInline]

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
  list_display = ('name',)
  inlines = [BoardInline]

@admin.register(TerraGreen)
class TerraGreenAdmin(admin.ModelAdmin):
  list_display = ('name',)
  inlines = [BoardInline]

@admin.register(Tests)
class TestsAdmin(admin.ModelAdmin):
  inlines = [LogInline]
  

