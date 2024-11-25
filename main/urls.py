from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .views import *

"""
В этом файле прописываются url адреса для HTML страниц и эндпоинты для REST
"""


router = routers.DefaultRouter()
router.register(r'type', TypeViewSet, basename='type')
router.register(r'models', ModViewSet, basename='models')
router.register(r'company', CompanyViewSet, basename='company')

urlpatterns = [

    path('api/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path("", Homing.as_view(), name="homing"),
    path("", include(router.urls)),
    path("<slug:slug>", Homing.as_view(), name="homing"),
    path("<slug:slug>/", MainPage.as_view(), name="category_detail"),
    path("<slug:slug>/search/", SearchResults.as_view(), name='searchresults'),
    path("<slug:slug>/<slug:cat_slug>", CategoryPage.as_view(), name='category'),




]

