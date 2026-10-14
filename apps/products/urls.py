from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # ---------- Client ----------
    path('', views.ProductListView.as_view(), name='list'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),

    # ---------- Dashboard: Products ----------
    path('dashboard/products/', views.DashboardProductListView.as_view(), name='dashboard_list'),
    path('dashboard/products/add/', views.DashboardProductCreateView.as_view(), name='dashboard_add'),
    path('dashboard/products/<int:pk>/edit/', views.DashboardProductUpdateView.as_view(), name='dashboard_edit'),
    path('dashboard/products/<int:pk>/delete/', views.DashboardProductDeleteView.as_view(), name='dashboard_delete'),
    path('dashboard/import-csv/', views.ProductCSVImportView.as_view(), name='csv_import'),

    # ---------- Dashboard: Categories ----------
    path('dashboard/categories/', views.DashboardCategoryListView.as_view(), name='dashboard_category_list'),
    path('dashboard/categories/add/', views.DashboardCategoryCreateView.as_view(), name='dashboard_category_add'),
    path('dashboard/categories/<int:pk>/edit/', views.DashboardCategoryUpdateView.as_view(), name='dashboard_category_edit'),
    path('dashboard/categories/<int:pk>/delete/', views.DashboardCategoryDeleteView.as_view(), name='dashboard_category_delete'),

    # ---------- Dashboard: Media Management ----------
    path('dashboard/media/<int:pk>/delete/', views.ProductMediaDeleteView.as_view(), name='media_delete'),
    path('dashboard/media/<int:pk>/set-cover/', views.ProductMediaSetCoverView.as_view(), name='media_set_cover'),
    path('dashboard/media/reorder/', views.ProductMediaReorderView.as_view(), name='media_reorder'),
]