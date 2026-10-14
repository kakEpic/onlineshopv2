"""
Product CSV Import Service
"""
import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

from .models import Category, Product


@dataclass
class RowError:
    row_number: int
    handle: str
    message: str
    is_warning: bool = False


@dataclass
class ImportResult:
    total_rows: int = 0
    products_created: int = 0
    products_updated: int = 0
    categories_created: int = 0
    skipped: int = 0
    errors: list[RowError] = field(default_factory=list)

    @property
    def has_errors(self):
        return any(not e.is_warning for e in self.errors)

    @property
    def has_warnings(self):
        return any(e.is_warning for e in self.errors)

    @property
    def error_count(self):
        return sum(1 for e in self.errors if not e.is_warning)

    @property
    def warning_count(self):
        return sum(1 for e in self.errors if e.is_warning)

    @property
    def success_count(self):
        return self.products_created + self.products_updated


class ProductCSVImporter:
    REQUIRED_COLUMNS = ['Handle', 'Option 1 value', 'Price [Cosvita ]']

    def __init__(self, file_content: str):
        self.file_content = file_content
        self.result = ImportResult()
        self._category_cache = {}

    def run(self) -> ImportResult:
        try:
            rows = self._parse_csv()
        except Exception as e:
            self.result.errors.append(RowError(
                row_number=0, handle='',
                message=f'CSV parse error: {str(e)}'
            ))
            return self.result

        grouped = self._group_by_handle(rows)
        for handle, group_rows in grouped.items():
            self._process_product_group(handle, group_rows)

        return self.result

    def _parse_csv(self) -> list[dict]:
        sample = self.file_content[:5000]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',\t')
        except csv.Error:
            dialect = csv.excel_tab

        reader = csv.DictReader(io.StringIO(self.file_content), dialect=dialect)

        if reader.fieldnames is None:
            raise ValueError('CSV ទទេ ឬ format មិនត្រឹមត្រូវ')

        reader.fieldnames = [f.strip() for f in reader.fieldnames]

        missing = [col for col in self.REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise ValueError(f'CSV ខ្វះ columns: {", ".join(missing)}')

        rows = list(reader)
        self.result.total_rows = len(rows)
        return rows

    def _group_by_handle(self, rows: list[dict]) -> dict[str, list[dict]]:
        grouped = {}
        for idx, row in enumerate(rows, start=2):
            handle = (row.get('Handle') or '').strip()
            if not handle:
                self.result.errors.append(RowError(
                    row_number=idx, handle='',
                    message='Handle ទទេ - skip row'
                ))
                self.result.skipped += 1
                continue

            row['_row_number'] = idx
            grouped.setdefault(handle, []).append(row)

        return grouped

    def _process_product_group(self, handle: str, rows: list[dict]):
        try:
            retail_rows = self._find_rows_by_keyword(rows, ['retail'])
            wholesale_rows = self._find_rows_by_keyword(rows, ['wholesale', 'wh'])

            if not retail_rows and not wholesale_rows:
                retail_rows = [rows[0]]
                self.result.errors.append(RowError(
                    row_number=rows[0]['_row_number'], handle=handle,
                    message='⚠️ មិនមាន retail/wholesale option - យក row ដំបូងជា retail',
                    is_warning=True,
                ))

            retail_row = retail_rows[0] if retail_rows else None
            wholesale_row = wholesale_rows[0] if wholesale_rows else None

            if len(retail_rows) > 1:
                self.result.errors.append(RowError(
                    row_number=retail_rows[0]['_row_number'], handle=handle,
                    message=f'⚠️ មាន retail variants {len(retail_rows)} - យក "{retail_rows[0].get("Option 1 value", "").strip()}"',
                    is_warning=True,
                ))
            if len(wholesale_rows) > 1:
                self.result.errors.append(RowError(
                    row_number=wholesale_rows[0]['_row_number'], handle=handle,
                    message=f'⚠️ មាន wholesale variants {len(wholesale_rows)} - យក "{wholesale_rows[0].get("Option 1 value", "").strip()}"',
                    is_warning=True,
                ))

            name_row = self._find_row_with_name(rows)
            if not name_row:
                self.result.errors.append(RowError(
                    row_number=rows[0]['_row_number'], handle=handle,
                    message='គ្មាន row ណាមួយមាន Name - skip product'
                ))
                self.result.skipped += 1
                return

            name = (name_row.get('Name') or '').strip()
            category_name = (name_row.get('Category') or '').strip()
            description = (name_row.get('Description') or '').strip()

            if not category_name:
                category_name = 'Uncategorized'
                self.result.errors.append(RowError(
                    row_number=name_row['_row_number'], handle=handle,
                    message='⚠️ Category ទទេ - assign to "Uncategorized"',
                    is_warning=True,
                ))

            barcode = ''
            for source_row in [retail_row, wholesale_row, name_row]:
                if source_row:
                    barcode = (source_row.get('Barcode') or '').strip()
                    if barcode:
                        break

            price_retail = None
            retail_sale_type = ''
            if retail_row:
                try:
                    price_retail = self._parse_decimal(retail_row.get('Price [Cosvita ]'))
                    retail_sale_type = (retail_row.get('Option 1 value') or '').strip()
                except ValueError as e:
                    self.result.errors.append(RowError(
                        row_number=retail_row['_row_number'], handle=handle,
                        message=f'Retail price error: {str(e)}'
                    ))

            price_wholesale = None
            wholesale_sale_type = ''
            if wholesale_row:
                try:
                    price_wholesale = self._parse_decimal(wholesale_row.get('Price [Cosvita ]'))
                    wholesale_sale_type = (wholesale_row.get('Option 1 value') or '').strip()
                except ValueError:
                    pass

            if price_retail is None and price_wholesale is None:
                self.result.errors.append(RowError(
                    row_number=rows[0]['_row_number'], handle=handle,
                    message='គ្មាន price ទាំង retail និង wholesale - skip product'
                ))
                self.result.skipped += 1
                return

            if price_retail is None:
                price_retail = price_wholesale
                retail_sale_type = wholesale_sale_type
                price_wholesale = None
                wholesale_sale_type = ''
                self.result.errors.append(RowError(
                    row_number=rows[0]['_row_number'], handle=handle,
                    message='⚠️ គ្មាន retail price - យក wholesale ជា retail',
                    is_warning=True,
                ))

            category = self._get_or_create_category(category_name)

            self._save_product(
                handle=handle,
                name=name,
                description=description,
                barcode=barcode,
                category=category,
                price_retail=price_retail,
                price_wholesale=price_wholesale,
                retail_sale_type=retail_sale_type,
                wholesale_sale_type=wholesale_sale_type,
                row_number=name_row['_row_number'],
            )

        except Exception as e:
            self.result.errors.append(RowError(
                row_number=rows[0].get('_row_number', 0), handle=handle,
                message=f'Unexpected error: {str(e)}'
            ))
            self.result.skipped += 1

    def _find_rows_by_keyword(self, rows: list[dict], keywords: list[str]) -> list[dict]:
        keywords = [k.lower() for k in keywords]
        matched = []
        for row in rows:
            value = (row.get('Option 1 value') or '').strip().lower()
            if any(kw in value for kw in keywords):
                matched.append(row)
        return matched

    def _find_row_with_name(self, rows: list[dict]) -> Optional[dict]:
        for row in rows:
            name = (row.get('Name') or '').strip()
            if name:
                return row
        return None

    def _parse_decimal(self, value) -> Decimal:
        if value is None or str(value).strip() == '':
            raise ValueError('តម្លៃ​ទទេ')
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            raise ValueError(f'តម្លៃមិនត្រឹមត្រូវ: {value}')

    def _get_or_create_category(self, name: str) -> Category:
        if name in self._category_cache:
            return self._category_cache[name]

        category, created = Category.all_objects.get_or_create(name=name)
        if category.is_deleted:
            category.is_deleted = False
            category.deleted_at = None
            category.save(update_fields=['is_deleted', 'deleted_at'])

        if created:
            self.result.categories_created += 1

        self._category_cache[name] = category
        return category

    def _save_product(self, handle, name, description, barcode, category,
                       price_retail, price_wholesale,
                       retail_sale_type='', wholesale_sale_type='', row_number=0):
        active_product = Product.objects.filter(handle=handle, is_deleted=False).first()
        if active_product:
            self.result.skipped += 1
            self.result.errors.append(RowError(
                row_number=row_number,
                handle=handle,
                message='⚠️ Product មានរួចហើយ (active) - skip (មិន update)',
                is_warning=True,
            ))
            return

        deleted_product = Product.objects.filter(handle=handle, is_deleted=True).first()
        if deleted_product:
            archived_handle = f'{handle}-deleted-{deleted_product.pk}'
            deleted_product.handle = archived_handle
            deleted_product.save(update_fields=['handle', 'updated_at'])
            self.result.errors.append(RowError(
                row_number=row_number,
                handle=handle,
                message='⚠️ Product soft-deleted មានស្រាប់ - បង្កើត product ថ្មី',
                is_warning=True,
            ))

        Product.objects.create(
            handle=handle,
            name=name,
            description=description,
            barcode=barcode,
            category=category,
            price_retail=price_retail,
            price_wholesale=price_wholesale,
            retail_sale_type=retail_sale_type,
            wholesale_sale_type=wholesale_sale_type,
            is_visible_to_client=True,
            is_deleted=False,
        )
        self.result.products_created += 1