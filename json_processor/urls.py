from django.conf.urls import url
from json_processor import views

app_name = 'json_processor'
urlpatterns =[
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^upload_data/$', views.UploadDataView.as_view(), name='upload_data'),
    url(r'^start_test/$', views.StartTestView.as_view(), name='start_test'),
    url(r'^show_test_info/(?P<test_request>\d+)/$', views.ShowTestInfoView.as_view(), name='show_test_info'),
]
