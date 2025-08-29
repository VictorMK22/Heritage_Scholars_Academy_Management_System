from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    # Fee listing and management
    path('', views.fee_list, name='fee_list'),
    path('create/', views.create_fee, name='create_fee'),
    path('<int:pk>/', views.fee_detail, name='fee_detail'),
    path('<int:pk>/update/', views.update_fee, name='update_fee'),
    path('<int:pk>/delete/', views.delete_fee, name='delete_fee'),
    path('<int:pk>/mark-paid/', views.mark_fee_paid, name='mark_fee_paid'),
    
    # Student-specific fee views
    path('student/<int:student_id>/', views.student_fee_list, name='student_fee_list'),
    path('student/<int:student_id>/create/', views.create_student_fee, name='create_student_fee'),
    
    # Bulk operations
    path('bulk-create/', views.bulk_create_fees, name='bulk_create_fees'),
    path('bulk-update/', views.bulk_update_fees, name='bulk_update_fees'),
    
    # Reports and exports
    path('report/overview/', views.fee_overview_report, name='fee_overview_report'),
    path('report/unpaid/', views.unpaid_fees_report, name='unpaid_fees_report'),
    path('export/', views.export_fees, name='export_fees'),
    
    # Payment processing
    path('<int:pk>/payment/', views.process_payment, name='process_payment'),
    path('payment/history/', views.payment_history, name='payment_history'),
    
    # Due date management
    path('upcoming-due/', views.upcoming_due_fees, name='upcoming_due_fees'),
    path('overdue/', views.overdue_fees, name='overdue_fees'),

    # Admin fee management
    path('admin/fees/fee/<int:pk>/pay/', FeeAdmin.admin_site.admin_view(FeeAdmin.mark_paid_view),
         name='fees_fee_pay'),
    
    # API endpoints (if needed)
    path('api/fees/', views.FeeListAPI.as_view(), name='fee_api_list'),
    path('api/fees/<int:pk>/', views.FeeDetailAPI.as_view(), name='fee_api_detail'),
]