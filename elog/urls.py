from django.urls import path
from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('boards', views.BoardListView.as_view(), name='boards'),
  path('board/<int:pk>', views.BoardDetailView.as_view(), name='board-detail'),
  path('logs', views.LogListView.as_view(), name='logs'),
  path('log/<int:pk>', views.LogDetailView.as_view(), name='log-detail'),
  path('log/create/', views.LogCreate.as_view(), name='log-create'),
  path('log/<int:pk>/update/', views.LogUpdate.as_view(), name='log-update'),
  path('log/<int:pk>/delete/', views.LogDelete.as_view(), name='log-delete'),
]
