from django.contrib import admin

# Register your models here.
from .models import BoardType, Board, Location, TerraGreen, Log, BoardStatus, Tests, TestResult
from .test_status import update_board_test_status

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
  list_display = (
    'board_type', 'board_id', 'location', 'terragreen', 'r455_replaced',
    'ucsb_test_status', 'ucsb_status_auto_update',
    'b904_test_status', 'b904_status_auto_update',
  )
  list_filter = (
    'board_type', 'location', 'terragreen', 'r455_replaced',
    'ucsb_test_status', 'ucsb_status_auto_update',
    'b904_test_status', 'b904_status_auto_update',
  )
  inlines = [LogInline]

  def save_model(self, request, obj, form, change):
    for site in ('ucsb', 'b904'):
      status_field = f'{site}_test_status'
      auto_field = f'{site}_status_auto_update'
      status_changed = status_field in form.changed_data
      auto_enabled_now = auto_field in form.changed_data and getattr(obj, auto_field)
      if status_changed:
        selected_status = getattr(obj, status_field)
        if selected_status == Board.TestStatus.TEST_STAND:
          setattr(obj, auto_field, False)
        elif selected_status == Board.TestStatus.UNDER_REPAIRING:
          setattr(obj, auto_field, True)
        elif not auto_enabled_now:
          setattr(obj, auto_field, False)
    super().save_model(request, obj, form, change)
    for site in ('ucsb', 'b904'):
      update_board_test_status(obj, site)

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
  
