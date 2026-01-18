# test_security.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from secure_uploads.validators import validate_image_upload
from django.core.exceptions import ValidationError


class SecureUploadTests(TestCase):
    def test_rejects_php_disguised_as_jpg(self):
        """Malicious PHP file with .jpg extension should be rejected."""
        fake_image = SimpleUploadedFile(
            "hack.jpg", b"<?php echo 'pwned'; ?>", content_type="image/jpeg"
        )

        with self.assertRaises(ValidationError):
            validate_image_upload(fake_image)

    def test_rejects_oversized_file(self):
        """Files over the size limit should be rejected."""
        # Create a file that's too large
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        large_file = SimpleUploadedFile(
            "large.jpg", large_content, content_type="image/jpeg"
        )

        with self.assertRaises(ValidationError):
            validate_image_upload(large_file)
