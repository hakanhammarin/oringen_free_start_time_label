from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime, timedelta
import csv

# === CONFIGURATION ===
label_width = 38 * mm
label_height = 21.2 * mm
margin_x = 10 * mm
margin_y = 10 * mm
cols = 5
rows_total = 13
header_rows = 1
usable_rows = rows_total - header_rows
labels_per_page = cols * usable_rows

debug_mode = False  # Toggle to False for production output

# === TIME HELPERS ===
def parse_time(tstr):
    return datetime.strptime(tstr.strip(), "%H:%M")

def generate_time_slots(start, end, step_minutes=1):
    current = start
    while current <= end:
        yield current.strftime("%H:%M")
        current += timedelta(minutes=step_minutes)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return 0, 0, 0  # default to black
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

# === DRAWING ===
def draw_header(c, class_name, page_number=None):
    c.setFont("Helvetica-Bold", 25)
    x_center = margin_x + (cols * label_width) / 2
    y = A4[1] - margin_y - label_height + 7
    c.drawCentredString(x_center, y, f"{class_name}")
    
    if debug_mode and page_number is not None:
        c.setFont("Helvetica", 8)
        c.drawRightString(A4[0] - margin_x, margin_y / 2, f"Page {page_number}")

def draw_label(c, x, y, time_str, day, class_name, row=None, col=None, text_rgb=(0,0,0)):
    r, g, b = text_rgb
    c.setFillColorRGB(r, g, b)  # ensure text is colored correctly

    # Optional debug grid
#    if debug_mode:
#        c.setStrokeGray(0.8)
#        c.setLineWidth(0.3)
#        c.rect(x, y - label_height, label_width, label_height, stroke=1, fill=0)
#        if row is not None and col is not None:
#            c.setFont("Helvetica", 6)
#            c.setFillGray(0.5)
#            c.drawString(x + 2 * mm, y - label_height + 2 * mm, f"R{row} C{col}")
#            c.setFillColorRGB(r, g, b)  # restore label text color    # Optional debug grid

    padding = 3 * mm
    third = label_height / 3

    # Line 1: Class (left)
    c.setFont("Helvetica", 10)
    y1 = y - label_height + padding + 2 * third
    c.drawString(x + padding, y1, class_name)

    # Line 2: Time (centered, large)
    c.setFont("Helvetica-Bold", 25)
    y2 = y - label_height + padding - 5 + third
    c.drawCentredString(x + label_width / 2, y2, time_str)

    # Line 3: Day (right)
    c.setFont("Helvetica", 10)
    y3 = y - label_height + padding
    c.drawRightString(x + label_width - padding, y3, f"{day}")

# === MAIN PDF GENERATOR ===

def generate_labels(csv_path, output_pdf, step_minutes=1):
    c = canvas.Canvas(output_pdf, pagesize=A4)

    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if rows and rows[0][0].lower().strip() == "class":
            rows = rows[1:]

    page_counter = 1
    first_page = True

    for row in rows:
        if len(row) < 5:
            print(f"Skipping malformed row: {row}")
            continue

        class_name, start_str, end_str, day, hex_color = [cell.strip() for cell in row]
        start = parse_time(start_str)
        end = parse_time(end_str)
        time_slots = list(generate_time_slots(start, end, step_minutes))

        r, g, b = hex_to_rgb(hex_color)

        # Start a fresh page for this class
        if not first_page:
            c.showPage()
            page_counter += 1
        else:
            first_page = False

        page_counter += 1
        c.setFillColorRGB(r, g, b)
        draw_header(c, class_name, page_number=page_counter)

        for i, time_str in enumerate(time_slots):
            # Position on page relative to label grid (excluding header row)
            pos = i % labels_per_page
            col = pos % cols
            row_num = pos // cols  # 0-based row under header row

            # Start new page if label exceeds current page capacity
            if i != 0 and pos == 0:
                c.showPage()
                page_counter += 1
                c.setFillColorRGB(r, g, b)
                draw_header(c, class_name, page_number=page_counter)

            x = margin_x + col * label_width
            # Y starts from below header row, so add header height
            y = A4[1] - margin_y - label_height * (row_num + 1)   # extra label_height for header row space

            draw_label(c, x, y, time_str, day, class_name, row=row_num, col=col, text_rgb=(r, g, b))

    c.save()
    print(f"✅ PDF created: {output_pdf}")

# === RUN EXAMPLE ===
if __name__ == "__main__":
    generate_labels("label_pages.csv", "etiketter_output.pdf", step_minutes=1)