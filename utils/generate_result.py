from utils.error_message import show_error_message
from utils.validators import validate_fields, validate_images

def generate_result(page):
    """
    Validates inputs, initiates the backend session in a background thread,
    and transitions to the preview page with loading animation.
    """
    # 1. Validate Images
    missing_images = validate_images(page.before_btn, page.after_btn)
    if missing_images:
        show_error_message(page, "Missing Images", "Please upload:\n• " + "\n• ".join(missing_images))
        return

    # 2. Validate Form Fields
    fields = page.form_fields.get_fields()
    empty_fields = validate_fields(fields)
    if empty_fields:
        show_error_message(page, "Incomplete Form", "Please fill:\n• " + "\n• ".join(empty_fields))
        return

    # 3. Get form data and store in session manager
    form_data = page.form_fields.get_data()
    page.session_manager.set_form_data(form_data)

    # 4. Get image paths
    before_path = page.before_btn.toolTip()
    after_path = page.after_btn.toolTip()

    # 5. Switch to preview page and start processing with loading animation
    if page.parent():
        main_window = page.parent().parent()
        
        if hasattr(main_window, 'stack') and hasattr(main_window, 'preview_page'):
            # Switch to preview page first (will show loading animation)
            main_window.stack.setCurrentWidget(main_window.preview_page)
            # Start background processing with loading animation
            main_window.preview_page.start_processing(before_path, after_path)