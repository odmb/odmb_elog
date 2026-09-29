from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from .models import Board, Log, Tests
from .test_status import initialize_existing_board_test_statuses, update_all_board_test_statuses


def _update_board(board_id):
  board = Board.objects.filter(pk=board_id).first()
  if board is not None:
    update_all_board_test_statuses(board)


@receiver(post_save, sender=Log)
def update_status_after_log_save(sender, instance, **kwargs):
  _update_board(instance.board_id)


@receiver(post_delete, sender=Log)
def update_status_after_log_delete(sender, instance, **kwargs):
  _update_board(instance.board_id)


@receiver(post_save, sender=Tests)
def update_status_after_test_save(sender, instance, **kwargs):
  board_id = Log.objects.filter(tests_id=instance.pk).values_list('board_id', flat=True).first()
  if board_id is not None:
    _update_board(board_id)


@receiver(post_migrate)
def initialize_statuses_after_migrate(sender, app_config, **kwargs):
  if app_config is not None and app_config.name == 'elog':
    initialize_existing_board_test_statuses()
