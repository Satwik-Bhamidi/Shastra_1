from styles.theme import *
def validate_fields(fields):
    """Validate that all form fields are filled"""
    empty = [name for field, name in fields if not field.text().strip()]
    return empty


def validate_images(before_btn, after_btn):
    """Validate that both images are uploaded"""
    missing_images = []
    if not before_btn.toolTip():
        missing_images.append("Before Firing Image")
    if not after_btn.toolTip():
        missing_images.append("After Firing Image")
    return missing_images



