from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(filename, text, size=(400, 400), bg_color=(60, 42, 77), text_color=(255, 255, 255)):
    # Create new image with background color
    image = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(image)
    
    # Calculate text size and position
    try:
        font = ImageFont.truetype("Arial", 40)
    except:
        font = ImageFont.load_default()
        
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill=text_color)
    
    # Save image
    image.save(filename)

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the newOy directory
    newoy_dir = os.path.dirname(script_dir)
    # Path to products directory
    products_dir = os.path.join(newoy_dir, 'static', 'img', 'products')
    
    # Create directory if it doesn't exist
    os.makedirs(products_dir, exist_ok=True)
    
    # List of images to create
    images = [
        ('vinyl1.jpg', 'Vinyl Record'),
        ('poetry-event.jpg', 'Poetry Event'),
        ('tshirt1.jpg', 'Ahoy T-Shirt'),
        ('art-print1.jpg', 'Art Print'),
        ('workshop1.jpg', 'Workshop'),
        ('digital-album1.jpg', 'Digital Album'),
        ('photo1.jpg', 'Concert Photo'),
        ('tote1.jpg', 'Tote Bag')
    ]
    
    # Create each placeholder image
    for filename, text in images:
        filepath = os.path.join(products_dir, filename)
        create_placeholder(filepath, text)
        print(f'Created {filename}')

if __name__ == '__main__':
    main() 