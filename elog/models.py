from django.db import models
from django.urls import reverse
import datetime

# Create your models here.
class Location(models.Model):
  """Model representing location of board."""
  name = models.CharField(max_length=200, help_text='Enter a location for boards')

  def __str__(self):
    """String for representing Model object."""
    return self.name


class BoardType(models.Model):
  """Model representing type of board."""
  name = models.CharField(max_length=200, help_text='Enter board type')
  description = models.TextField(help_text='Enter description of board type', null=True, blank=True)

  def __str__(self):
    """String for representing Model object."""
    return self.name


class Board(models.Model):
  """Model representing each board."""
  board_id = models.IntegerField(help_text="Board ID")
  board_type = models.ForeignKey('BoardType', on_delete=models.RESTRICT)
  location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
  status = models.ForeignKey('BoardStatus', on_delete=models.SET_NULL, null=True, blank=True)

  def get_absolute_url(self):
    """Returns the URL to access a particular instance of the model."""
    return reverse('board-detail', args=[str(self.id)])

  class Meta:
    ordering = ['board_type', 'board_id']

  def __str__(self):
    """String for representing Model object."""
    return f"{self.board_type}#{self.board_id}"


def get_now():
  return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

class Log(models.Model):
  """Model representing a log."""
  id = models.AutoField(help_text="log ID", primary_key=True)
  board = models.ForeignKey('Board', on_delete=models.CASCADE)
  date = models.DateTimeField(default=get_now, help_text="Format is YYYY-MM-DD HH:MM")
  location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="board location")
  file = models.FileField(null=True, blank=True)
  text = models.TextField(null=True, blank=True, verbose_name="log")
  status = models.ForeignKey('BoardStatus', on_delete=models.SET_NULL, null=True, blank=True)

  class Meta:
    ordering = ['-date']

  def __str__(self):
    """String for representing Model object."""
    return str(self.id)

  def get_absolute_url(self):
    """Returns the URL to access a particular instance of the model."""
    return reverse('log-detail', args=[str(self.id)])


class BoardStatus(models.Model):
  """Model representing board status."""

  status = models.CharField(max_length=200, help_text='Enter board status')

  def __str__(self):
    """String for representing Model object."""
    return self.status
