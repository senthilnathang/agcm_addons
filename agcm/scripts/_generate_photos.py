"""Generate placeholder construction site photos for demo data.

Creates actual image files stored in uploads/agcm/photos/ and
links them via documents_document records to agcm_photos records.
"""

import hashlib
import io
import os
import random
import uuid
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


PHOTO_SUBJECTS = [
    "Foundation work", "Steel erection", "Concrete pour", "Framing progress",
    "Exterior wall", "Roof installation", "Plumbing rough-in", "Electrical conduit",
    "HVAC ductwork", "Drywall installation", "Painting in progress", "Flooring layout",
    "Window installation", "Landscaping work", "Parking lot paving",
    "Elevator shaft", "Stairwell construction", "Fire sprinkler pipes",
    "Restroom tile work", "Lobby finishing", "Loading dock area",
    "Equipment on site", "Material delivery", "Scaffolding setup",
    "Excavation work", "Utility trenching", "Waterproofing membrane",
    "Masonry wall", "Glass curtain wall", "Mechanical room equipment",
    "Ceiling grid install", "Signage brackets", "Courtyard pavers",
    "Retaining wall", "Storm drain work", "Curb and gutter",
    "Sidewalk pour", "Fence installation", "Gate mechanism",
    "Exterior lighting", "Interior lighting fixtures", "Cabinet installation",
    "Countertop fitting", "Door hardware", "Handrail welding",
    "Rebar placement", "Form work setup", "Crane operation",
    "Safety netting", "Debris removal", "Site cleanup progress",
]

ALBUMS = [
    "Exterior", "Interior", "Foundation", "Structure", "MEP",
    "Finishing", "Landscape", "Site Work", "Equipment", "Progress",
]

# Colors for placeholder images — simulating construction site tones
BG_COLORS = [
    (139, 119, 101),  # tan/dirt
    (169, 169, 169),  # concrete gray
    (101, 130, 152),  # steel blue
    (143, 161, 126),  # construction green
    (178, 147, 115),  # sand/wood
    (120, 100, 85),   # brown
    (160, 140, 130),  # warm gray
    (110, 140, 160),  # sky blue-gray
    (150, 120, 100),  # rust
    (130, 150, 140),  # sage
]

ACCENT_COLORS = [
    (255, 165, 0),   # safety orange
    (255, 255, 0),   # caution yellow
    (0, 100, 200),   # blue
    (200, 50, 50),   # red
    (80, 80, 80),    # dark gray
]


def _create_placeholder_image(subject: str, location: str, width=800, height=600) -> bytes:
    """Generate a placeholder construction photo image."""
    bg = random.choice(BG_COLORS)
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Draw some construction-like geometric shapes
    for _ in range(random.randint(3, 8)):
        accent = random.choice(ACCENT_COLORS)
        shape_type = random.choice(["rect", "line", "rect", "line", "rect"])
        if shape_type == "rect":
            x1 = random.randint(0, width - 100)
            y1 = random.randint(0, height - 80)
            x2 = x1 + random.randint(50, 300)
            y2 = y1 + random.randint(30, 200)
            if random.random() > 0.5:
                draw.rectangle([x1, y1, x2, y2], outline=accent, width=2)
            else:
                fill = tuple(max(0, c - 30) for c in bg)
                draw.rectangle([x1, y1, x2, y2], fill=fill, outline=accent, width=1)
        elif shape_type == "line":
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([x1, y1, x2, y2], fill=accent, width=random.randint(1, 3))

    # Add text overlay
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_small = font

    # Subject label
    text_bg = Image.new("RGBA", (width, 70), (0, 0, 0, 140))
    img.paste(Image.new("RGB", (width, 70), tuple(max(0, c - 60) for c in bg)), (0, height - 70))
    draw.text((20, height - 60), subject, fill=(255, 255, 255), font=font)
    draw.text((20, height - 30), f"Location: {location}", fill=(200, 200, 200), font=font_small)

    # Date stamp top-right
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((width - 200, 10), stamp, fill=(255, 255, 200), font=font_small)

    # AGCM watermark
    draw.text((20, 10), "AG|CM Site Photo", fill=(255, 255, 255, 180), font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return buf.getvalue()


def generate_photos(db, log_ids, company_id, user_id, locations):
    """Generate photo records with actual image files for demo data.

    Uses raw SQL to avoid ORM relationship resolution issues in standalone scripts.
    """
    from sqlalchemy import text

    uploads_base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'uploads')
    uploads_base = os.path.abspath(uploads_base)

    photo_count = 0
    batch_size = 50

    for log_id, pid, log_date in log_ids:
        num_photos = random.randint(1, 3)
        for _ in range(num_photos):
            photo_count += 1
            subject = random.choice(PHOTO_SUBJECTS)
            location = random.choice(locations)
            album = random.choice(ALBUMS)

            # Generate image
            img_bytes = _create_placeholder_image(subject, location)
            img_hash = hashlib.sha256(img_bytes).hexdigest()

            # Save to filesystem
            date_dir = log_date.strftime("%Y/%m/%d")
            photo_dir = os.path.join(uploads_base, "agcm", "photos", date_dir)
            os.makedirs(photo_dir, exist_ok=True)

            unique_id = uuid.uuid4().hex[:12]
            filename = f"site_photo_{unique_id}.jpg"
            filepath = os.path.join(photo_dir, filename)
            with open(filepath, "wb") as f:
                f.write(img_bytes)

            storage_key = f"agcm/photos/{date_dir}/{filename}"
            file_url = f"/uploads/{storage_key}"

            # Insert document record via raw SQL
            document_id = None
            try:
                result = db.execute(text("""
                    INSERT INTO documents_document
                        (name, original_filename, mime_type, size, hash, file_extension,
                         storage_key, storage_backend, status, category, owner_id, company_id,
                         current_version_number)
                    VALUES
                        (:name, :filename, 'image/jpeg', :size, :hash, 'jpg',
                         :storage_key, 'local', 'active', 'other', :owner_id, :company_id, 1)
                    RETURNING id
                """), {
                    "name": subject, "filename": filename, "size": len(img_bytes),
                    "hash": img_hash, "storage_key": storage_key,
                    "owner_id": user_id, "company_id": company_id,
                })
                row = result.fetchone()
                if row:
                    document_id = row[0]
            except Exception:
                pass

            # Insert photo record via raw SQL
            db.execute(text("""
                INSERT INTO agcm_photos
                    (company_id, sequence_name, name, file_name, location, album,
                     document_id, file_url, dailylog_id, project_id, created_by)
                VALUES
                    (:company_id, :seq, :name, :filename, :location, :album,
                     :doc_id, :file_url, :dailylog_id, :project_id, :user_id)
            """), {
                "company_id": company_id,
                "seq": f"PH{photo_count:05d}",
                "name": subject,
                "filename": filename,
                "location": location,
                "album": album,
                "doc_id": document_id,
                "file_url": file_url,
                "dailylog_id": log_id,
                "project_id": pid,
                "user_id": user_id,
            })

            if photo_count % batch_size == 0:
                db.commit()
                print(f"    ... {photo_count} photos generated")

    db.commit()
    print(f"    Created {photo_count} photos with image files")
    return photo_count
