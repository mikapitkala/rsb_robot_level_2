from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Archive import Archive
from RPA.Tables import Tables
from RPA.Excel.Files import Files
from RPA.PDF import PDF

import re

shopURL = "https://robotsparebinindustries.com/#/robot-order"
ordersURL = "https://robotsparebinindustries.com/orders.csv"

@task

def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    get_rid_of_modal()
    download_csv_orders()
    orders = get_orders()

    for order_number, order in enumerate(orders, start=1):
        fill_the_form(order)
        preview_robot()
        submit_order()
        validate_order()
        
        order_number = None
        while not order_number:
            order_number = get_order_number()
            if not order_number:
                submit_order()
                validate_order()
        
        pdf_file = f"output/{order_number}.pdf"
        screenshot_file = f"output/robot_{order_number}.png"
        
        store_as_pdf(order_number)
        screenshot_robot(order_number)
        embed_screenshot_to_receipt(f"output/robot_{order_number}.png", f"output/{order_number}.pdf")
        order_another_robot()
    archive_receipts()


def open_robot_order_website():
    """Navigate to shop"""
    browser.goto(shopURL)
    page = browser.page()
    
    
def get_rid_of_modal():
    """ Select OK to give up all constitutional rights """
    page = browser.page()
    page.click("button:text('OK')")


def download_csv_orders():
    """Download the updated orders file"""
    http = HTTP()
    http.download(ordersURL, "orders.csv")

def get_orders():
    """Read orders from the CSV file"""
    tables = Tables()
    orders = tables.read_table_from_csv("orders.csv")
    return orders

def fill_the_form(order):
    """Fill in the order form with data from a single order"""
    page = browser.page()
    page.select_option("select#head", order['Head'])
    body_id = f"id-body-{order['Body']}"
    page.click(f"input#{body_id}")
    page.fill("input[placeholder='Enter the part number for the legs']", str(order['Legs']))
    page.fill("input#address", order['Address'])

def preview_robot():
    """Preview the robot"""
    pass
    page = browser.page()
    page.click("button:text('Preview')")

def submit_order():
    """Submit the order"""
    page = browser.page()
    page.click("button:text('ORDER')")

def validate_order():
    """Make sure order went though, hit ORDER again, if not"""
    # class="alert alert-danger" if error
    page = browser.page()
    while True:
        if page.query_selector(".alert.alert-danger"):
            submit_order()
        else:
            break

def get_order_number():
    """Extract the order number from the page content"""
    page = browser.page()
    content = page.content()
    match = re.search(r"RSB-ROBO-ORDER-\w+", content)
    if match:
        return match.group(0)
    else:
        return None

def store_as_pdf(order_number):
    """Save the order receipt as a PDF using the given order number"""
    page = browser.page()
    
    html = page.locator("#receipt").inner_html()
    
    pdf = PDF()
    pdf.html_to_pdf(html, f"output/{order_number}.pdf")

def screenshot_robot(order_number):
    """Take a screenshot of the ordered robot"""
    page = browser.page()
    element = page.locator("#robot-preview-image")
    element.screenshot(path=f"output/robot_{order_number}.png")

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Embed the screenshot to the PDF receipt"""
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(
        image_path=screenshot,
        source_path=pdf_file,
        output_path=f"{pdf_file}"
    )

def order_another_robot():
    """Order another robot"""
    page = browser.page()
    page.click("button:text('ORDER ANOTHER ROBOT')")
    get_rid_of_modal()

def archive_receipts():
    """Create a ZIP archive of the receipts"""
    archive = Archive()
    archive.archive_folder_with_zip("output", "output/receipts.zip", include="*.pdf", recursive=False)