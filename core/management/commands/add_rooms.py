from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from room_management.models import Room
from PIL import Image, ImageDraw, ImageFont
import os
import io

class Command(BaseCommand):
    help = 'Add 20 diverse rooms with complete information and generated images'

    def handle(self, *args, **options):
        # First, delete the test room
        Room.objects.filter(room_number='TEST-001').delete()
        
        # Room configurations
        room_configs = [
            # Study Rooms (5 rooms)
            {
                'name': 'Silent Study Room A', 'number': 'SS-101', 'type': 'study', 'capacity': 8,
                'location': 'First Floor, East Wing', 'color': '#2E8B57',
                'facilities': 'Individual study desks, Silent zone, Natural lighting, Power outlets, WiFi, Air conditioning, Personal lockers',
                'description': 'A quiet study space designed for individual focused work with minimal distractions.'
            },
            {
                'name': 'Group Study Room B', 'number': 'GS-102', 'type': 'study', 'capacity': 12,
                'location': 'First Floor, West Wing', 'color': '#228B22',
                'facilities': 'Collaborative tables, Whiteboard, Markers, WiFi, Comfortable seating, Group work tools',
                'description': 'Perfect for collaborative study sessions and group projects with flexible seating arrangements.'
            },
            {
                'name': 'Advanced Study Lab', 'number': 'AS-201', 'type': 'study', 'capacity': 15,
                'location': 'Second Floor, North Wing', 'color': '#32CD32',
                'facilities': 'Research databases access, Individual workstations, Charging stations, Ergonomic chairs, Task lighting',
                'description': 'Equipped with advanced research tools and databases for graduate-level study and research.'
            },
            {
                'name': 'Quiet Zone Study Room', 'number': 'QZ-103', 'type': 'study', 'capacity': 6,
                'location': 'First Floor, Central', 'color': '#90EE90',
                'facilities': 'Sound-proofed walls, Individual carrels, Reading lamps, Silent keyboards, No-phone policy',
                'description': 'Ultra-quiet environment for deep concentration and intensive study sessions.'
            },
            {
                'name': 'Graduate Study Lounge', 'number': 'GL-301', 'type': 'study', 'capacity': 20,
                'location': 'Third Floor, South Wing', 'color': '#00FF7F',
                'facilities': 'Comfortable seating, Coffee station, Reference materials, WiFi, Discussion areas, Phone booths',
                'description': 'Relaxed study environment with amenities for extended study sessions and informal discussions.'
            },

            # Meeting Rooms (4 rooms)
            {
                'name': 'Executive Conference Room', 'number': 'EC-401', 'type': 'meeting', 'capacity': 16,
                'location': 'Fourth Floor, Executive Suite', 'color': '#1E90FF',
                'facilities': 'Mahogany conference table, Leather chairs, 65-inch 4K display, Video conferencing, Climate control, Catering setup',
                'description': 'Premium meeting space for executive meetings and important presentations with high-end amenities.'
            },
            {
                'name': 'Team Collaboration Hub', 'number': 'TC-202', 'type': 'meeting', 'capacity': 10,
                'location': 'Second Floor, Innovation Wing', 'color': '#4169E1',
                'facilities': 'Modular furniture, Multiple whiteboards, Sticky walls, Standing desks, Collaboration tools, Creative supplies',
                'description': 'Dynamic space designed for brainstorming, creative sessions, and agile team meetings.'
            },
            {
                'name': 'Department Meeting Room', 'number': 'DM-204', 'type': 'meeting', 'capacity': 12,
                'location': 'Second Floor, Academic Wing', 'color': '#0000FF',
                'facilities': 'Oval meeting table, Ergonomic chairs, Projector, Screen, Teleconferencing, Note-taking supplies',
                'description': 'Standard meeting room ideal for departmental meetings and academic discussions.'
            },
            {
                'name': 'Quick Meeting Pod', 'number': 'QM-105', 'type': 'meeting', 'capacity': 6,
                'location': 'First Floor, Near Reception', 'color': '#6495ED',
                'facilities': 'Round table, Modern chairs, Wall-mounted display, Quick-connect ports, Soundproofing',
                'description': 'Compact meeting space perfect for quick discussions and small team check-ins.'
            },

            # Conference Rooms (4 rooms)
            {
                'name': 'Grand Auditorium', 'number': 'GA-501', 'type': 'conference', 'capacity': 200,
                'location': 'Fifth Floor, Main Hall', 'color': '#800080',
                'facilities': 'Theater seating, Stage, Professional lighting, Sound system, Live streaming, Recording equipment, Presenter tools',
                'description': 'Large auditorium perfect for conferences, seminars, and major academic events.'
            },
            {
                'name': 'Symposium Hall', 'number': 'SH-502', 'type': 'conference', 'capacity': 80,
                'location': 'Fifth Floor, East Hall', 'color': '#9932CC',
                'facilities': 'Tiered seating, Dual projectors, Microphone system, Registration desk, Refreshment area, A/V control booth',
                'description': 'Mid-sized conference room ideal for symposiums, workshops, and academic presentations.'
            },
            {
                'name': 'Seminar Theater', 'number': 'ST-401', 'type': 'conference', 'capacity': 50,
                'location': 'Fourth Floor, Theater Wing', 'color': '#8A2BE2',
                'facilities': 'Amphitheater seating, Smart board, Wireless presentation, Recording capability, Accessibility features',
                'description': 'Theater-style room designed for seminars and interactive presentations with excellent acoustics.'
            },
            {
                'name': 'Multi-Purpose Conference Room', 'number': 'MP-503', 'type': 'conference', 'capacity': 120,
                'location': 'Fifth Floor, Flexible Space', 'color': '#9400D3',
                'facilities': 'Configurable seating, Multiple screens, Breakout spaces, Catering kitchen, Storage, Movable partitions',
                'description': 'Versatile conference space that can be reconfigured for various event types and sizes.'
            },

            # Computer Labs (4 rooms)
            {
                'name': 'Programming Lab Alpha', 'number': 'PL-301', 'type': 'computer', 'capacity': 30,
                'location': 'Third Floor, Tech Wing', 'color': '#FF4500',
                'facilities': 'High-spec PCs, Multiple monitors, Development software, Server access, Network storage, Printing station',
                'description': 'Advanced programming lab with latest hardware and software for computer science courses.'
            },
            {
                'name': 'Digital Media Studio', 'number': 'DM-302', 'type': 'computer', 'capacity': 20,
                'location': 'Third Floor, Creative Wing', 'color': '#FF6347',
                'facilities': 'Workstations with graphics cards, Design software, Tablets, Scanners, 3D printers, Color-accurate monitors',
                'description': 'Specialized lab for digital media creation, graphic design, and multimedia projects.'
            },
            {
                'name': 'Research Computing Center', 'number': 'RC-303', 'type': 'computer', 'capacity': 15,
                'location': 'Third Floor, Research Wing', 'color': '#FF8C00',
                'facilities': 'High-performance workstations, Research software, Data analysis tools, Collaboration displays, Secure access',
                'description': 'Specialized computing facility for research projects requiring high computational power.'
            },
            {
                'name': 'General Computer Lab', 'number': 'GC-104', 'type': 'computer', 'capacity': 25,
                'location': 'First Floor, Public Access', 'color': '#FFA500',
                'facilities': 'Standard PCs, Office software, Internet access, Printing, Scanning, Basic productivity tools',
                'description': 'General-purpose computer lab for basic computing needs and general student use.'
            },

            # Reading Rooms (3 rooms)
            {
                'name': 'Main Reading Hall', 'number': 'MR-001', 'type': 'reading', 'capacity': 150,
                'location': 'Ground Floor, Central Library', 'color': '#DC143C',
                'facilities': 'Individual reading desks, Natural lighting, Silent environment, Reference access, Study carrels, Climate control',
                'description': 'Large, peaceful reading hall with traditional library atmosphere perfect for quiet reading.'
            },
            {
                'name': 'Periodical Reading Room', 'number': 'PR-002', 'type': 'reading', 'capacity': 40,
                'location': 'Ground Floor, Magazine Section', 'color': '#B22222',
                'facilities': 'Magazine racks, Newspaper stands, Comfortable chairs, Current publications, Archive access, Reading lights',
                'description': 'Dedicated space for reading current periodicals, newspapers, and magazines.'
            },
            {
                'name': 'Rare Books Reading Room', 'number': 'RB-003', 'type': 'reading', 'capacity': 12,
                'location': 'Ground Floor, Special Collections', 'color': '#8B0000',
                'facilities': 'Controlled environment, Security cameras, Archival furniture, White gloves provided, Restricted access, Preservation tools',
                'description': 'Secure reading room for accessing rare books and special collections with preservation protocols.'
            }
        ]

        self.stdout.write('Starting to create 20 rooms with images...')

        for i, config in enumerate(room_configs, 1):
            # Check if room already exists
            if Room.objects.filter(room_number=config['number']).exists():
                self.stdout.write(f"Room {config['number']} already exists, skipping...")
                continue

            # Generate room image
            image_data = self.generate_room_image(
                config['name'], 
                config['type'], 
                config['color'],
                config['capacity']
            )

            # Create room
            room = Room.objects.create(
                room_name=config['name'],
                room_number=config['number'],
                room_type=config['type'],
                capacity=config['capacity'],
                location=config['location'],
                facilities=config['facilities'],
                description=config['description'],
                status='available',
                is_active=True
            )

            # Save the generated image
            if image_data:
                filename = f"room_{config['number'].replace('-', '_').lower()}.png"
                room.cover_image.save(filename, ContentFile(image_data), save=True)

            self.stdout.write(f"✓ Created room {i}/20: {config['name']} ({config['number']})")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(room_configs)} rooms with complete information and images!')
        )

    def generate_room_image(self, room_name, room_type, color, capacity):
        """Generate a room cover image using Pillow"""
        try:
            # Create image
            width, height = 800, 600
            
            # Convert hex color to RGB
            color = color.lstrip('#')
            rgb_color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            img = Image.new('RGB', (width, height), rgb_color)
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for y in range(height):
                alpha = 1 - (y / height * 0.3)
                gradient_color = tuple(int(c * alpha) for c in rgb_color)
                draw.line([(0, y), (width, y)], fill=gradient_color)

            # Try to load fonts, fallback to default if not available
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                type_font = ImageFont.truetype("arial.ttf", 36)
                detail_font = ImageFont.truetype("arial.ttf", 24)
            except:
                # Use default font if arial is not available
                title_font = ImageFont.load_default()
                type_font = ImageFont.load_default() 
                detail_font = ImageFont.load_default()

            # Add room type badge
            type_display = {
                'study': '📚 STUDY ROOM',
                'meeting': '🤝 MEETING ROOM', 
                'conference': '🎯 CONFERENCE ROOM',
                'computer': '💻 COMPUTER LAB',
                'reading': '📖 READING ROOM'
            }.get(room_type, room_type.upper())

            # Calculate text dimensions
            try:
                type_bbox = draw.textbbox((0, 0), type_display, font=type_font)
                type_width = type_bbox[2] - type_bbox[0]
            except:
                type_width = len(type_display) * 20  # Fallback calculation

            # Draw type badge background
            badge_padding = 20
            badge_x = (width - type_width) // 2 - badge_padding
            badge_y = 50
            badge_width = type_width + badge_padding * 2
            badge_height = 60
            
            draw.rectangle(
                [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
                fill=(255, 255, 255, 200)
            )
            
            # Draw type text
            draw.text(
                ((width - type_width) // 2, badge_y + 15),
                type_display,
                font=type_font,
                fill=(50, 50, 50)
            )

            # Draw room name (split into lines if too long)
            lines = []
            words = room_name.split()
            current_line = ""
            
            for word in words:
                test_line = f"{current_line} {word}".strip()
                try:
                    test_bbox = draw.textbbox((0, 0), test_line, font=title_font)
                    test_width = test_bbox[2] - test_bbox[0]
                except:
                    test_width = len(test_line) * 30  # Fallback
                    
                if test_width <= width - 100:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)

            # Draw name background and text
            total_text_height = len(lines) * 60
            name_y_start = height // 2 - total_text_height // 2
            
            for j, line in enumerate(lines):
                try:
                    line_bbox = draw.textbbox((0, 0), line, font=title_font)
                    line_width = line_bbox[2] - line_bbox[0]
                except:
                    line_width = len(line) * 30  # Fallback
                    
                text_x = (width - line_width) // 2
                text_y = name_y_start + j * 60
                
                # Text shadow
                draw.text((text_x + 3, text_y + 3), line, font=title_font, fill=(0, 0, 0))
                # Main text
                draw.text((text_x, text_y), line, font=title_font, fill='white')

            # Draw capacity info
            capacity_text = f"Capacity: {capacity} people"
            try:
                capacity_bbox = draw.textbbox((0, 0), capacity_text, font=detail_font)
                capacity_width = capacity_bbox[2] - capacity_bbox[0]
            except:
                capacity_width = len(capacity_text) * 15  # Fallback
            
            capacity_y = height - 100
            draw.rectangle(
                [(width - capacity_width) // 2 - 15, capacity_y - 10, 
                 (width - capacity_width) // 2 + capacity_width + 15, capacity_y + 35],
                fill=(0, 0, 0)
            )
            
            draw.text(
                ((width - capacity_width) // 2, capacity_y),
                capacity_text,
                font=detail_font,
                fill='white'
            )

            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=95)
            return buffer.getvalue()

        except Exception as e:
            self.stdout.write(f"Warning: Could not generate image for {room_name}: {e}")
            return None
