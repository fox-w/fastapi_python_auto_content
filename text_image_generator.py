import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re

def create_text_image(text, output_filename="output.png", font_path=None, font_size=60, 
                     width=1080, height=1350, bg_color=(0, 0, 0), text_color=(255, 255, 255),
                     logo_path="logo/visionary.mindset_logo_simpler_redo.png", 
                     logo_opacity=0.75, add_logo=True):
    """
    Create an image with text on a solid background.
    
    Args:
        text (str): The text to display on the image
                   Use {word} for bold text and \\n for newlines
        output_filename (str): Filename to save the image
        font_path (str): Path to the font file (.ttf, .otf)
        font_size (int): Size of the font
        width (int): Width of the image in pixels
        height (int): Height of the image in pixels
        bg_color (tuple): RGB tuple for background color
        text_color (tuple): RGB tuple for text color
        logo_path (str): Path to the logo image
        logo_opacity (float): Opacity of the logo (0.0 to 1.0)
        add_logo (bool): Whether to add the logo overlay
    """
    # Create a blank image with the specified background color
    image = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to load regular and bold fonts
    try:
        if font_path and os.path.exists(font_path):
            regular_font_path = font_path
            # Try to find a bold version by name convention
            font_dir = os.path.dirname(font_path)
            font_name = os.path.basename(font_path)
            font_name_no_ext = os.path.splitext(font_name)[0]
            
            # Common bold font naming patterns
            bold_patterns = [
                f"{font_name_no_ext}-Bold.ttf", f"{font_name_no_ext}Bold.ttf",
                f"{font_name_no_ext}-Bold.otf", f"{font_name_no_ext}Bold.otf",
                f"{font_name_no_ext} Bold.ttf", f"{font_name_no_ext} Bold.otf"
            ]
            
            bold_font_path = None
            for pattern in bold_patterns:
                possible_path = os.path.join(font_dir, pattern)
                if os.path.exists(possible_path):
                    bold_font_path = possible_path
                    break
            
            regular_font = ImageFont.truetype(regular_font_path, font_size)
            bold_font = ImageFont.truetype(bold_font_path, font_size) if bold_font_path else regular_font
        else:
            # Try standard fonts
            standard_fonts = ["arial.ttf", "Arial.ttf", "calibri.ttf", "Calibri.ttf", 
                             "times.ttf", "Times New Roman.ttf"]
            standard_bold_fonts = ["arialbd.ttf", "Arial Bold.ttf", "calibrib.ttf", "Calibri Bold.ttf", 
                                  "timesbd.ttf", "Times New Roman Bold.ttf"]
            
            regular_font_loaded = False
            bold_font_loaded = False
            regular_font = None
            bold_font = None
            
            for i, font_name in enumerate(standard_fonts):
                try:
                    regular_font = ImageFont.truetype(font_name, font_size)
                    regular_font_loaded = True
                    
                    # Try to load corresponding bold font
                    if i < len(standard_bold_fonts):
                        try:
                            bold_font = ImageFont.truetype(standard_bold_fonts[i], font_size)
                            bold_font_loaded = True
                        except IOError:
                            pass
                    
                    break
                except IOError:
                    continue
            
            if not regular_font_loaded:
                regular_font = ImageFont.load_default()
                print("Using default font. Custom or standard fonts not found.")
            
            if not bold_font_loaded:
                bold_font = regular_font
                print("Using regular font for bold text. Bold font not found.")
    except Exception as e:
        print(f"Font error: {e}. Using default font.")
        regular_font = ImageFont.load_default()
        bold_font = regular_font
    
    # Process text - replace literal \n with actual newlines
    text = text.replace("\\n", "\n")
    
    # Calculate the maximum width for text wrapping
    max_width = width - 100  # Add some margin
    
    # Split text into lines by newline character
    lines = text.split("\n")
    formatted_lines = []
    
    # Process each line
    for line in lines:
        # Wrap the text to fit the width (initial estimate)
        initial_wrapper = textwrap.TextWrapper(width=max_width // (font_size // 2))
        wrapped_lines = initial_wrapper.wrap(line)
        
        # Add each wrapped line to the formatted lines
        for wrapped_line in wrapped_lines:
            formatted_lines.append(wrapped_line)
    
    # Calculate total height needed
    text_height = 0
    line_spacing = int(font_size * 0.3)  # 30% of font size for spacing
    
    # Use a list to store rendering instructions
    render_instructions = []
    
    # Calculate positions and store rendering instructions
    y_position = 0
    
    for line in formatted_lines:
        # Process text for bold formatting
        parts = []
        current_position = 0
        
        # Find all occurrences of {text}
        pattern = r'\{([^}]*)\}'
        for match in re.finditer(pattern, line):
            # Add text before the match
            if match.start() > current_position:
                normal_text = line[current_position:match.start()]
                if normal_text:
                    parts.append(("normal", normal_text))
            
            # Add the bold text (without the braces)
            bold_text = match.group(1)
            if bold_text:
                parts.append(("bold", bold_text))
            
            current_position = match.end()
        
        # Add any remaining text
        if current_position < len(line):
            parts.append(("normal", line[current_position:]))
        
        # If no formatting is found, add the whole line as normal
        if not parts:
            parts.append(("normal", line))
        
        # Calculate total width of the line
        line_width = 0
        for style, text_part in parts:
            font_to_use = bold_font if style == "bold" else regular_font
            part_width = draw.textlength(text_part, font=font_to_use)
            line_width += part_width
        
        # Calculate starting x position to center the line
        x_position = (width - line_width) // 2
        
        # Add rendering instructions for each part
        for style, text_part in parts:
            font_to_use = bold_font if style == "bold" else regular_font
            part_width = draw.textlength(text_part, font=font_to_use)
            
            render_instructions.append((text_part, font_to_use, (x_position, y_position)))
            x_position += part_width
        
        # Move to next line
        y_position += font_size + line_spacing
        text_height += font_size + line_spacing
    
    # Center the entire text block vertically
    y_offset = (height - text_height) // 2
    
    # Draw the text based on instructions
    for text_part, font, (x, y) in render_instructions:
        draw.text((x, y + y_offset), text_part, font=font, fill=text_color)
    
    # Add logo if requested and the logo file exists
    if add_logo and logo_path and os.path.exists(logo_path):
        try:
            # Open the logo image
            logo = Image.open(logo_path)
            
            # Calculate a reasonable size for the logo (e.g., 25% of the width)
            logo_width = int(width * 0.20)
            logo_height = int(logo_width * logo.height / logo.width)
            
            # Resize the logo
            logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
            
            # If the logo has an alpha channel (transparency), use it
            if logo.mode == 'RGBA':
                # Create a mask from the alpha channel
                mask = logo.split()[3]
                
                # Apply opacity to the mask
                if logo_opacity < 1.0:
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Brightness(mask)
                    mask = enhancer.enhance(logo_opacity)
            else:
                # Create a new image with an alpha channel for opacity
                logo_with_opacity = Image.new('RGBA', logo.size)
                
                # Fill with the logo but adjust alpha
                for x in range(logo.width):
                    for y in range(logo.height):
                        r, g, b = logo.getpixel((x, y))
                        logo_with_opacity.putpixel((x, y), (r, g, b, int(255 * logo_opacity)))
                
                logo = logo_with_opacity
                mask = logo.split()[3]
            
            # Calculate position (bottom center)
            logo_x = (width - logo_width) // 2
            logo_y = height - logo_height - 50  # 50 pixels from bottom
            
            # Paste the logo onto the image using the mask for transparency
            image.paste(logo.convert('RGB'), (logo_x, logo_y), mask)
            
            print(f"Logo added with {int(logo_opacity * 100)}% opacity")
        except Exception as e:
            print(f"Error adding logo: {e}")
    
    # Save the image
    image.save(output_filename)
    print(f"Image saved as {output_filename}")
    return image

def list_available_fonts(fonts_dir="fonts"):
    """List available fonts in the fonts directory"""
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
        print(f"Created '{fonts_dir}' directory. Place your font files (.ttf, .otf) here.")
        return []
    
    font_files = [f for f in os.listdir(fonts_dir) 
                 if f.lower().endswith(('.ttf', '.otf'))]
    
    if not font_files:
        print(f"No font files found in '{fonts_dir}' directory.")
    else:
        print("\nAvailable fonts:")
        for i, font in enumerate(font_files, 1):
            print(f"{i}. {font}")
    
    return font_files

if __name__ == "__main__":
    # Create fonts directory if it doesn't exist
    fonts_dir = "fonts"
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
        print(f"Created '{fonts_dir}' directory. Place your font files (.ttf, .otf) here.")
    
    # Default logo path
    default_logo_path = "logo/visionary.mindset_logo_simpler_redo.png"
    
    # Example usage with formatted text
    if input("Run example with formatted text and logo? (y/n): ").lower().strip() == 'y':
        text = "Your {vision} is worthless\\nwithout {relentless} execution."
        create_text_image(
            text, 
            "formatted_text_with_logo.png",
            logo_path=default_logo_path,
            logo_opacity=0.75
        )
    
    # Interactive mode
    if input("Do you want to enter custom text? (y/n): ").lower().strip() == 'y':
        print("Enter your text (use {word} for bold text and \\n for newlines):")
        custom_text = input()
        output_file = input("Enter output filename (default: custom_text.png): ") or "custom_text.png"
        
        # Font selection
        font_files = list_available_fonts(fonts_dir)
        font_path = None
        
        if font_files:
            use_custom_font = input("Do you want to use a custom font? (y/n): ").lower().strip() == 'y'
            if use_custom_font:
                try:
                    font_choice = int(input(f"Select font number (1-{len(font_files)}): "))
                    if 1 <= font_choice <= len(font_files):
                        font_path = os.path.join(fonts_dir, font_files[font_choice-1])
                        print(f"Using font: {font_files[font_choice-1]}")
                    else:
                        print("Invalid selection. Using default font.")
                except ValueError:
                    print("Invalid input. Using default font.")
        
        # Font size
        try:
            font_size = int(input("Enter font size (default: 60): ") or "60")
        except ValueError:
            font_size = 60
            print("Invalid input. Using default font size: 60")
        
        # Logo options
        add_logo = input("Add logo to the image? (y/n): ").lower().strip() == 'y'
        logo_path = None
        logo_opacity = 0.75
        
        if add_logo:
            # Check if default logo exists
            if os.path.exists(default_logo_path):
                use_default_logo = input(f"Use default logo ({default_logo_path})? (y/n): ").lower().strip() == 'y'
                if use_default_logo:
                    logo_path = default_logo_path
                else:
                    logo_path = input("Enter custom logo path: ")
            else:
                logo_path = input("Default logo not found. Enter custom logo path: ")
            
            # Get opacity
            try:
                opacity_pct = input("Enter logo opacity percentage (default: 75): ") or "75"
                logo_opacity = float(opacity_pct) / 100.0
                # Clamp to valid range
                logo_opacity = max(0.0, min(1.0, logo_opacity))
            except ValueError:
                logo_opacity = 0.75
                print("Invalid input. Using default opacity: 75%")
        
        create_text_image(
            custom_text, 
            output_file, 
            font_path, 
            font_size,
            logo_path=logo_path if add_logo else None,
            logo_opacity=logo_opacity,
            add_logo=add_logo
        ) 