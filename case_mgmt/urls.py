# case_mgmt/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('', views.home_view, name='home'),
    path('ipfs-connect/', views.ipfs_connect_view, name='ipfs_connect'),
    path('create-case/', views.create_case_view, name='create_case'),
    path('case/<int:case_id>/', views.case_detail_view, name='case_detail'),
    path('my-cases/', views.my_cases_view, name='my_cases'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('case/<int:case_id>/delete/', views.delete_case_view, name='delete_case'),
    path('case/<int:case_id>/update/', views.update_case_view, name='update_case'),
    path('case/<int:case_id>/upload-file/', views.upload_file_view, name='upload_file'),
  
]