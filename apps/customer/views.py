from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)

from .models import Customer
from .forms import CustomerForm


class CustomerListView(ListView):
    model = Customer
    template_name = 'customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20


class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customer_list')


class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customer_list')


class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'customers/delete.html'
    success_url = reverse_lazy('customer_list')