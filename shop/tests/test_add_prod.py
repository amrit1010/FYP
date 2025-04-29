from django.test import TestCase
from django.contrib.auth import get_user_model
from shop.models import Category, Brand, Size, Product
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ProductModelTest(TestCase):
    def setUp(self):
        print("\nSetting up test environment...")
        self.vendor = User.objects.create_user(
            email='email@vendor.com',
            password='testpass',
            full_name='Vendor Name',
            phone='1234567890',)
        print(f"Created vendor: {self.vendor.email}")
        self.category = Category.objects.create(name="Electronics")
        print(f"Created category: {self.category.name}")
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x89\x61\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            content_type='image/jpeg')
        self.brand = Brand.objects.create(name="Samsung", image=image)
        print(f"Created brand: {self.brand.name}")
        self.size = Size.objects.create(name="Medium")
        print(f"Created size: {self.size.name}")
    def test_add_product(self):
        print("\nTesting product creation...")
        product = Product.objects.create(
            vendor=self.vendor,
            name="Samsung Galaxy", description="Latest Samsung phone", additional_information="Includes charger",
            price=50000.00,discount=1000.00,availability=True,sku="SGX123",size=self.size, features=True,
            categories=self.category, stock=10, brand=self.brand, product_type=Product.SELLING, status='approved')
        print("Product created successfully!")
        print(f"Checking product name: {product.name}")
        self.assertEqual(product.name, "Samsung Galaxy")
        print(f"Checking availability: {product.availability}")
        self.assertTrue(product.availability)
        product_count = Product.objects.count()
        print(f"Total products in DB: {product_count}")
        self.assertEqual(product_count, 1)
