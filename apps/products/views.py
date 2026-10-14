"""
Products app views - CBV
"""
import os
import subprocess
import tempfile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.files import File
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, UpdateView,
)

from .forms import ProductCSVImportForm, ProductForm, ProductMediaForm


def _generate_video_poster(media_instance):
    """
    Extract first frame from video using ffmpeg (if available).
    Saves the thumbnail to media_instance.video_poster and returns True on success.
    """
    try:
        video_path = media_instance.file.path
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        result = subprocess.run(
            [
                'ffmpeg', '-y',
                '-i', video_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', 'scale=800:800:force_original_aspect_ratio=decrease',
                '-q:v', '3',
                tmp_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            with open(tmp_path, 'rb') as f:
                fname = f'poster_{media_instance.pk}.jpg'
                media_instance.video_poster.save(fname, File(f), save=True)
            os.unlink(tmp_path)
            return True
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return False
from .models import Category, Product, ProductMedia
from .services import ProductCSVImporter


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for admin-only views"""

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, 'អ្នកមិនមាន permission ដើម្បីចូល page នេះ។')
        return super().handle_no_permission()


# ============================================================
# CSV Import (Admin)
# ============================================================
class ProductCSVImportView(AdminRequiredMixin, FormView):
    form_class = ProductCSVImportForm
    template_name = 'products/admin/csv_import.html'
    success_url = reverse_lazy('products:csv_import')

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']

        try:
            content = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(self.request, 'File មិន​មាន encoding UTF-8។')
            return self.form_invalid(form)

        importer = ProductCSVImporter(content)
        result = importer.run()

        context = self.get_context_data(form=ProductCSVImportForm())
        context['result'] = result
        context['filename'] = csv_file.name

        if result.success_count > 0:
            messages.success(
                self.request,
                f'Import រួចរាល់! Created: {result.products_created}, Skipped: {result.skipped}'
            )

        if result.has_errors:
            messages.error(self.request, f'មាន errors: {result.error_count} rows')
        if result.has_warnings:
            messages.warning(self.request, f'មាន warnings: {result.warning_count} cases')

        return render(self.request, self.template_name, context)


# ============================================================
# Client Side (Public)
# ============================================================
class ProductListView(ListView):
    model = Product
    template_name = 'products/client/list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    SORT_OPTIONS = {
        'newest': ('-created_at', 'Newest'),
        'price_low': ('price_retail', 'Price: Low to High'),
        'price_high': ('-price_retail', 'Price: High to Low'),
        'popular': ('-view_count', 'Most Popular'),
        'top_sales': ('-total_sold', 'Top Sales'),  # ADD THIS
        'name_asc': ('name', 'Name: A-Z'),
        'name_desc': ('-name', 'Name: Z-A'),
    }

    def get_queryset(self):
        qs = Product.objects.filter(is_visible_to_client=True, is_deleted=False).select_related('category')

        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__name__iexact=category_slug)

        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort in self.SORT_OPTIONS:
            qs = qs.order_by(self.SORT_OPTIONS[sort][0])
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'newest')
        ctx['sort_options'] = self.SORT_OPTIONS
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/client/detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_visible_to_client=True, is_deleted=False).select_related('category')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Product.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj


# ============================================================
# Dashboard CRUD (Admin)
# ============================================================
class DashboardProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'products/admin/list.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):
        qs = Product.objects.filter(is_deleted=False).select_related('category').order_by('-created_at')

        visibility = self.request.GET.get('visibility')
        if visibility == 'visible':
            qs = qs.filter(is_visible_to_client=True)
        elif visibility == 'hidden':
            qs = qs.filter(is_visible_to_client=False)

        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['visibility'] = self.request.GET.get('visibility', '')
        return ctx


class DashboardProductCreateView(AdminRequiredMixin, CreateView):
    """Create new product view"""
    model = Product
    form_class = ProductForm
    template_name = 'products/admin/form_create.html'
    
    def get_success_url(self):
        return reverse('products:dashboard_edit', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Auto-generate handle and slug if not provided
        product = form.save(commit=False)
        if not product.handle:
            base_slug = slugify(product.name)
            product.handle = base_slug
            # Ensure uniqueness
            counter = 1
            while Product.objects.filter(handle=product.handle).exists():
                product.handle = f"{base_slug}-{counter}"
                counter += 1
        
        if not product.slug:
            product.slug = product.handle
            counter = 1
            while Product.objects.filter(slug=product.slug).exists():
                product.slug = f"{product.handle}-{counter}"
                counter += 1
        
        product.save()
        
        # Handle multiple file uploads
        files = self.request.FILES.getlist('files')
        for idx, file in enumerate(files):
            ext = file.name.lower().split('.')[-1]
            media_type = 'video' if ext in ['mp4', 'webm', 'mov'] else 'image'
            media = ProductMedia.objects.create(
                product=product,
                media_type=media_type,
                file=file,
                alt_text=file.name,
                is_cover=(idx == 0),  # First file is cover
            )
            if media_type == 'video':
                _generate_video_poster(media)
        
        if files:
            messages.success(self.request, f'{len(files)} media file(s) uploaded.')
        messages.success(self.request, f'Product "{product.name}" created successfully!')

        if 'save_and_add' in self.request.POST:
            return redirect('products:dashboard_add')
        return redirect('products:dashboard_edit', pk=product.pk)


class DashboardProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    queryset = Product.objects.filter(is_deleted=False)
    form_class = ProductForm
    template_name = 'products/admin/form.html'
    
    def get_success_url(self):
        return reverse('products:dashboard_edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['product_media'] = self.object.media.all()
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle multiple file uploads
        files = self.request.FILES.getlist('files')
        for file in files:
            ext = file.name.lower().split('.')[-1]
            media_type = 'video' if ext in ['mp4', 'webm', 'mov'] else 'image'
            media = ProductMedia.objects.create(
                product=self.object,
                media_type=media_type,
                file=file,
                alt_text=file.name,
            )
            if media_type == 'video':
                _generate_video_poster(media)
        
        if files:
            messages.success(self.request, f'{len(files)} media file(s) uploaded.')
        messages.success(self.request, f'Product "{form.instance.name}" updated.')
        return response


class DashboardProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    queryset = Product.objects.filter(is_deleted=False)
    template_name = 'products/admin/confirm_delete.html'
    success_url = reverse_lazy('products:dashboard_list')

    def form_valid(self, form):
        messages.success(self.request, f'Product "{self.object.name}" deleted.')
        return super().form_valid(form)


# ============================================================
# Category Dashboard
# ============================================================
class DashboardCategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'products/admin/category_list.html'
    context_object_name = 'categories'


class DashboardCategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    template_name = 'products/admin/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('products:dashboard_category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created.')
        return super().form_valid(form)


class DashboardCategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    template_name = 'products/admin/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('products:dashboard_category_list')


class DashboardCategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'products/admin/category_confirm_delete.html'
    success_url = reverse_lazy('products:dashboard_category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{self.object.name}" has been hidden.')
        return super().form_valid(form)


# ============================================================
# Product Media Management (Admin)
# ============================================================
class ProductMediaDeleteView(AdminRequiredMixin, View):
    """Delete a product media item"""
    
    def post(self, request, pk):
        media = get_object_or_404(ProductMedia, pk=pk)
        product_pk = media.product.pk
        media.file.delete(save=False)  # Delete the actual file
        media.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Media deleted successfully.')
        return redirect('products:dashboard_edit', pk=product_pk)


class ProductMediaSetCoverView(AdminRequiredMixin, View):
    """Set a media item as cover"""
    
    def post(self, request, pk):
        media = get_object_or_404(ProductMedia, pk=pk)
        
        # Unset current cover for same media type
        ProductMedia.objects.filter(
            product=media.product,
            media_type=media.media_type,
            is_cover=True
        ).update(is_cover=False)
        
        # Set this as cover
        media.is_cover = True
        media.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Cover image updated.')
        return redirect('products:dashboard_edit', pk=media.product.pk)


class ProductMediaReorderView(AdminRequiredMixin, View):
    """Reorder media items via AJAX"""
    
    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            for idx, media_id in enumerate(order):
                ProductMedia.objects.filter(pk=media_id).update(display_order=idx)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)