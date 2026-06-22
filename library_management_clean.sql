-- =====================================================
-- Library Management System - MySQL Database Schema
-- Clean Installation Script for MySQL Workbench
-- Generated: June 10, 2025
-- =====================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS library_management_system
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE library_management_system;

-- =====================================================
-- CORE APP TABLES
-- =====================================================

-- UserProfile Table
CREATE TABLE core_userprofile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    phone_number VARCHAR(15) DEFAULT '',
    date_of_birth DATE NULL,
    address TEXT,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_core_userprofile_role CHECK (role IN ('student', 'staff', 'admin')),
    INDEX idx_core_userprofile_user_id (user_id),
    INDEX idx_core_userprofile_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Category Table
CREATE TABLE core_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_core_category_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Author Table
CREATE TABLE core_author (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    biography TEXT,
    birth_date DATE NULL,
    nationality VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_core_author_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Publisher Table
CREATE TABLE core_publisher (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    website VARCHAR(200) DEFAULT '',
    established_year INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_core_publisher_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Donation Table (created before Book because of foreign key)
CREATE TABLE core_donation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id_isbn VARCHAR(20) NOT NULL,
    title_of_book VARCHAR(300) NOT NULL,
    author_id INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    book_cover VARCHAR(100) DEFAULT '',
    donor_name VARCHAR(200) NOT NULL,
    donor_email VARCHAR(254) DEFAULT '',
    donor_phone VARCHAR(15) DEFAULT '',
    quantity INT UNSIGNED NOT NULL DEFAULT 1,
    state_of_book VARCHAR(20) NOT NULL DEFAULT 'good',
    donate_date DATE NOT NULL DEFAULT (CURDATE()),
    is_processed TINYINT(1) NOT NULL DEFAULT 0,
    notes TEXT,
    CONSTRAINT chk_core_donation_state CHECK (state_of_book IN ('excellent', 'good', 'fair', 'poor', 'damaged')),
    FOREIGN KEY (author_id) REFERENCES core_author(id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES core_publisher(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES core_category(id) ON DELETE CASCADE,
    INDEX idx_core_donation_date (donate_date),
    INDEX idx_core_donation_processed (is_processed),
    INDEX idx_core_donation_donor (donor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Book Table
CREATE TABLE core_book (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id_isbn VARCHAR(20) NOT NULL UNIQUE,
    title_of_book VARCHAR(300) NOT NULL,
    author_id INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    publication_date DATE NULL,
    pages INT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'English',
    description TEXT,
    state_of_book VARCHAR(20) NOT NULL DEFAULT 'good',
    image VARCHAR(100) DEFAULT '',
    is_available TINYINT(1) NOT NULL DEFAULT 1,
    is_from_donation TINYINT(1) NOT NULL DEFAULT 0,
    donation_source_id INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_core_book_state CHECK (state_of_book IN ('excellent', 'good', 'fair', 'poor', 'damaged')),
    FOREIGN KEY (author_id) REFERENCES core_author(id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES core_publisher(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES core_category(id) ON DELETE CASCADE,
    FOREIGN KEY (donation_source_id) REFERENCES core_donation(id) ON DELETE SET NULL,
    INDEX idx_core_book_title (title_of_book),
    INDEX idx_core_book_isbn (book_id_isbn),
    INDEX idx_core_book_available (is_available),
    INDEX idx_core_book_author (author_id),
    INDEX idx_core_book_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inventory Table
CREATE TABLE core_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL UNIQUE,
    total_copies INT UNSIGNED NOT NULL DEFAULT 1,
    available_copies INT UNSIGNED NOT NULL DEFAULT 1,
    borrowed_copies INT UNSIGNED NOT NULL DEFAULT 0,
    reserved_copies INT UNSIGNED NOT NULL DEFAULT 0,
    damaged_copies INT UNSIGNED NOT NULL DEFAULT 0,
    shelf_location VARCHAR(100) NOT NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES core_book(book_id) ON DELETE CASCADE,
    INDEX idx_core_inventory_available (available_copies),
    INDEX idx_core_inventory_location (shelf_location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recycle Table
CREATE TABLE core_recycle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NULL,
    book_id_isbn VARCHAR(20) NOT NULL,
    title VARCHAR(300) DEFAULT '',
    quantity INT UNSIGNED NOT NULL DEFAULT 1,
    reason VARCHAR(50) NOT NULL,
    description TEXT,
    recycled_by_id INT NOT NULL,
    date DATE NOT NULL DEFAULT (CURDATE()),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    disposal_date DATE NULL,
    disposal_method VARCHAR(100) DEFAULT '',
    disposal_notes TEXT,
    CONSTRAINT chk_core_recycle_reason CHECK (reason IN ('damaged', 'outdated', 'worn', 'lost', 'other')),
    CONSTRAINT chk_core_recycle_status CHECK (status IN ('pending', 'disposed', 'cancelled')),
    FOREIGN KEY (book_id) REFERENCES core_book(book_id) ON DELETE SET NULL,
    INDEX idx_core_recycle_status (status),
    INDEX idx_core_recycle_date (date),
    INDEX idx_core_recycle_reason (reason)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SystemLog Table
CREATE TABLE core_systemlog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(200) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45) NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_core_systemlog_timestamp (timestamp),
    INDEX idx_core_systemlog_user (user_id),
    INDEX idx_core_systemlog_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- STUDENT APP TABLES
-- =====================================================

-- Member Table
CREATE TABLE student_member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    member_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,
    gender VARCHAR(1) NOT NULL,
    age INT UNSIGNED NOT NULL,
    date_of_birth DATE NOT NULL,
    date_joined DATE NOT NULL DEFAULT (CURDATE()),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    max_books INT UNSIGNED NOT NULL DEFAULT 3,
    max_reservations INT UNSIGNED NOT NULL DEFAULT 2,
    CONSTRAINT chk_student_member_gender CHECK (gender IN ('M', 'F', 'O')),
    INDEX idx_student_member_id (member_id),
    INDEX idx_student_member_name (name),
    INDEX idx_student_member_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Borrow Table
CREATE TABLE student_borrow (
    borrow_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    date_borrow DATE NOT NULL DEFAULT (CURDATE()),
    date_due DATE NOT NULL,
    date_return DATE NULL,
    is_returned TINYINT(1) NOT NULL DEFAULT 0,
    renewal_count INT UNSIGNED NOT NULL DEFAULT 0,
    max_renewals INT UNSIGNED NOT NULL DEFAULT 2,
    notes TEXT,
    borrowed_by_staff_id INT NULL,
    FOREIGN KEY (member_id) REFERENCES student_member(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES core_book(book_id) ON DELETE CASCADE,
    INDEX idx_student_borrow_date (date_borrow),
    INDEX idx_student_borrow_due (date_due),
    INDEX idx_student_borrow_returned (is_returned),
    INDEX idx_student_borrow_member (member_id),
    INDEX idx_student_borrow_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reservation Table
CREATE TABLE student_reservation (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    date_reserved DATE NOT NULL DEFAULT (CURDATE()),
    date_expires DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    notes TEXT,
    CONSTRAINT chk_student_reservation_status CHECK (status IN ('active', 'fulfilled', 'cancelled', 'expired')),
    FOREIGN KEY (member_id) REFERENCES student_member(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES core_book(book_id) ON DELETE CASCADE,
    INDEX idx_student_reservation_status (status),
    INDEX idx_student_reservation_date (date_reserved),
    INDEX idx_student_reservation_expires (date_expires),
    INDEX idx_student_reservation_member (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fine Table
CREATE TABLE student_fine (
    fine_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    borrow_record_id INT NULL,
    fine_type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    date_imposed DATE NOT NULL DEFAULT (CURDATE()),
    date_paid DATE NULL,
    is_paid TINYINT(1) NOT NULL DEFAULT 0,
    payment_method VARCHAR(50) DEFAULT '',
    imposed_by_id INT NULL,
    CONSTRAINT chk_student_fine_type CHECK (fine_type IN ('overdue', 'damage', 'lost', 'late_return')),
    FOREIGN KEY (member_id) REFERENCES student_member(id) ON DELETE CASCADE,
    FOREIGN KEY (borrow_record_id) REFERENCES student_borrow(borrow_id) ON DELETE CASCADE,
    INDEX idx_student_fine_paid (is_paid),
    INDEX idx_student_fine_date (date_imposed),
    INDEX idx_student_fine_member (member_id),
    INDEX idx_student_fine_type (fine_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notification Table
CREATE TABLE student_notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    related_book_id INT NULL,
    related_room_booking_id INT NULL,
    CONSTRAINT chk_student_notification_type CHECK (notification_type IN ('book_due', 'book_overdue', 'reservation_ready', 'reservation_expired', 'fine_imposed', 'room_booking_approved', 'room_booking_cancelled', 'book_available', 'room_available', 'general')),
    FOREIGN KEY (member_id) REFERENCES student_member(id) ON DELETE CASCADE,
    FOREIGN KEY (related_book_id) REFERENCES core_book(book_id) ON DELETE SET NULL,
    INDEX idx_student_notification_read (is_read),
    INDEX idx_student_notification_created (created_at),
    INDEX idx_student_notification_member (member_id),
    INDEX idx_student_notification_type (notification_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- ROOM MANAGEMENT APP TABLES
-- =====================================================

-- Room Table
CREATE TABLE room_management_room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    room_type VARCHAR(20) NOT NULL,
    capacity INT UNSIGNED NOT NULL,
    location VARCHAR(200) NOT NULL,
    facilities TEXT,
    hourly_rate DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    cover_image VARCHAR(100) DEFAULT '',
    description TEXT,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_room_management_room_type CHECK (room_type IN ('study', 'meeting', 'conference', 'computer', 'reading')),
    CONSTRAINT chk_room_management_room_status CHECK (status IN ('available', 'occupied', 'maintenance', 'reserved')),
    INDEX idx_room_management_room_number (room_number),
    INDEX idx_room_management_room_type (room_type),
    INDEX idx_room_management_room_status (status),
    INDEX idx_room_management_room_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RoomEquipment Table
CREATE TABLE room_management_roomequipment (
    equipment_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    equipment_name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(20) NOT NULL,
    model_number VARCHAR(100) DEFAULT '',
    serial_number VARCHAR(100) DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'working',
    purchase_date DATE NULL,
    warranty_expires DATE NULL,
    last_maintenance DATE NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_room_management_equipment_type CHECK (equipment_type IN ('projector', 'computer', 'whiteboard', 'screen', 'microphone', 'speaker', 'camera', 'printer', 'other')),
    CONSTRAINT chk_room_management_equipment_status CHECK (status IN ('working', 'broken', 'maintenance', 'missing')),
    FOREIGN KEY (room_id) REFERENCES room_management_room(room_id) ON DELETE CASCADE,
    INDEX idx_room_management_equipment_room (room_id),
    INDEX idx_room_management_equipment_type (equipment_type),
    INDEX idx_room_management_equipment_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RoomBooking Table
CREATE TABLE room_management_roombooking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    booked_by_id INT NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    purpose VARCHAR(200) NOT NULL,
    attendees_count INT UNSIGNED NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    special_requirements TEXT,
    total_cost DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    approved_by_id INT NULL,
    date_booked TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_approved TIMESTAMP NULL,
    CONSTRAINT chk_room_management_booking_status CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),
    FOREIGN KEY (room_id) REFERENCES room_management_room(room_id) ON DELETE CASCADE,
    UNIQUE KEY uniq_admin_room_booking_time (room_id, booking_date, start_time),
    INDEX idx_room_management_booking_date (booking_date),
    INDEX idx_room_management_booking_status (status),
    INDEX idx_room_management_booking_booked_by (booked_by_id),
    INDEX idx_room_management_booking_room (room_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RoomMaintenance Table
CREATE TABLE room_management_roommaintenance (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    maintenance_type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    completed_date DATE NULL,
    is_completed TINYINT(1) NOT NULL DEFAULT 0,
    performed_by VARCHAR(200) NOT NULL,
    notes TEXT,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_room_management_maintenance_type CHECK (maintenance_type IN ('cleaning', 'repair', 'upgrade', 'inspection')),
    FOREIGN KEY (room_id) REFERENCES room_management_room(room_id) ON DELETE CASCADE,
    INDEX idx_room_management_maintenance_scheduled (scheduled_date),
    INDEX idx_room_management_maintenance_completed (is_completed),
    INDEX idx_room_management_maintenance_room (room_id),
    INDEX idx_room_management_maintenance_type (maintenance_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- ADMIN CUSTOM APP TABLES
-- =====================================================

-- Staff Table
CREATE TABLE admin_custom_staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    phone_number VARCHAR(15) DEFAULT '',
    emergency_contact VARCHAR(200) DEFAULT '',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_admin_custom_staff_employee_id (employee_id),
    INDEX idx_admin_custom_staff_department (department),
    INDEX idx_admin_custom_staff_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add the missing foreign key constraint after all tables are created
ALTER TABLE student_notification 
ADD CONSTRAINT fk_student_notification_room_booking 
FOREIGN KEY (related_room_booking_id) REFERENCES room_management_roombooking(booking_id) ON DELETE SET NULL;

-- =====================================================
-- SAMPLE DATA INSERTS
-- =====================================================

-- Insert sample categories
INSERT INTO core_category (name, description) VALUES
('Fiction', 'Fictional literature and novels'),
('Science', 'Scientific texts and research'),
('Technology', 'Technology and computer science books'),
('History', 'Historical texts and biographies'),
('Mathematics', 'Mathematical texts and references'),
('Art', 'Art and design books'),
('Business', 'Business and economics books'),
('Philosophy', 'Philosophy and ethics texts'),
('Biography', 'Biographical works and memoirs'),
('Reference', 'Reference materials and encyclopedias');

-- Insert sample authors
INSERT INTO core_author (name, biography, nationality) VALUES
('J.K. Rowling', 'British author, best known for Harry Potter series', 'British'),
('Stephen King', 'American author of horror and supernatural fiction', 'American'),
('Isaac Asimov', 'American science fiction writer and biochemist', 'American'),
('Agatha Christie', 'British crime writer, known for detective fiction', 'British'),
('Mark Twain', 'American writer and humorist', 'American'),
('Jane Austen', 'English novelist known for social commentary', 'British'),
('George Orwell', 'British author and journalist', 'British'),
('Charles Dickens', 'Victorian era English novelist', 'British'),
('Ernest Hemingway', 'American novelist and journalist', 'American'),
('William Shakespeare', 'English playwright and poet', 'British');

-- Insert sample publishers
INSERT INTO core_publisher (name, address, established_year) VALUES
('Penguin Random House', 'New York, USA', 1927),
('HarperCollins', 'London, UK', 1989),
('Oxford University Press', 'Oxford, UK', 1586),
('McGraw-Hill Education', 'New York, USA', 1888),
('Cambridge University Press', 'Cambridge, UK', 1534),
('Pearson Education', 'London, UK', 1844),
('Macmillan Publishers', 'London, UK', 1843),
('Wiley', 'Hoboken, USA', 1807),
('Springer', 'Berlin, Germany', 1842),
('Elsevier', 'Amsterdam, Netherlands', 1880);

-- Insert sample books
INSERT INTO core_book (book_id_isbn, title_of_book, author_id, publisher_id, category_id, publication_date, pages, description, state_of_book) VALUES
('978-0-7432-7356-5', 'Harry Potter and the Philosopher''s Stone', 1, 1, 1, '1997-06-26', 309, 'The first book in the Harry Potter series', 'excellent'),
('978-0-452-28423-4', 'The Shining', 2, 2, 1, '1977-01-28', 447, 'A psychological horror novel', 'good'),
('978-0-553-29337-0', 'Foundation', 3, 3, 1, '1951-05-01', 244, 'First book in the Foundation series', 'good'),
('978-0-06-112008-4', 'Murder on the Orient Express', 4, 2, 1, '1934-01-01', 256, 'A detective novel featuring Hercule Poirot', 'fair'),
('978-0-486-40077-3', 'The Adventures of Huckleberry Finn', 5, 4, 1, '1884-12-10', 366, 'Classic American literature', 'excellent');

-- Insert sample inventory for books
INSERT INTO core_inventory (book_id, total_copies, available_copies, shelf_location) VALUES
(1, 3, 2, 'A1-Fiction-001'),
(2, 2, 1, 'A1-Fiction-002'),
(3, 4, 4, 'B2-SciFi-001'),
(4, 2, 2, 'A1-Mystery-001'),
(5, 1, 1, 'C3-Classic-001');

-- Insert sample rooms
INSERT INTO room_management_room (room_name, room_number, room_type, capacity, location, facilities, hourly_rate, description) VALUES
('Study Room A', 'SR-001', 'study', 4, 'First Floor', 'Whiteboard, WiFi, Power outlets', 5.00, 'Quiet study room perfect for small groups'),
('Conference Hall', 'CH-101', 'conference', 50, 'Second Floor', 'Projector, Audio system, WiFi, Air conditioning', 25.00, 'Large conference room for presentations'),
('Computer Lab 1', 'CL-201', 'computer', 20, 'Third Floor', '20 Computers, Printer, WiFi, Software suite', 15.00, 'Fully equipped computer laboratory'),
('Meeting Room B', 'MR-102', 'meeting', 8, 'Second Floor', 'Video conferencing, Whiteboard, WiFi', 10.00, 'Professional meeting space'),
('Reading Hall', 'RH-001', 'reading', 100, 'Ground Floor', 'Natural lighting, Silent zone, WiFi', 0.00, 'Large quiet reading area'),
('Study Room B', 'SR-002', 'study', 6, 'First Floor', 'Whiteboard, WiFi, Comfortable seating', 5.00, 'Medium-sized study room for group work'),
('Seminar Room', 'SM-201', 'meeting', 15, 'Second Floor', 'Projector, Whiteboard, WiFi, Round table', 12.00, 'Perfect for seminars and workshops');

-- Insert sample room equipment
INSERT INTO room_management_roomequipment (room_id, equipment_name, equipment_type, model_number, status) VALUES
(1, 'Interactive Whiteboard', 'whiteboard', 'SMART-SB680', 'working'),
(2, 'HD Projector', 'projector', 'EPSON-EB-X41', 'working'),
(2, 'Sound System', 'speaker', 'BOSE-F1-812', 'working'),
(3, 'Desktop Computer Set 1', 'computer', 'DELL-OPTIPLEX-7090', 'working'),
(3, 'Laser Printer', 'printer', 'HP-LASERJET-P3015', 'working'),
(4, 'Video Conference Camera', 'camera', 'LOGITECH-RALLY', 'working'),
(5, 'Reading Lamps', 'other', 'PHILIPS-LED-DESK', 'working');

-- Insert sample members
INSERT INTO student_member (user_id, member_id, name, email, phone_number, address, gender, age, date_of_birth) VALUES
(101, 'MEM001', 'Alice Johnson', 'alice.johnson@email.com', '+1-555-0101', '123 Main St, City, State', 'F', 22, '2003-03-15'),
(102, 'MEM002', 'Bob Smith', 'bob.smith@email.com', '+1-555-0102', '456 Oak Ave, City, State', 'M', 24, '2001-07-22'),
(103, 'MEM003', 'Carol Davis', 'carol.davis@email.com', '+1-555-0103', '789 Pine Rd, City, State', 'F', 21, '2004-01-10'),
(104, 'MEM004', 'David Wilson', 'david.wilson@email.com', '+1-555-0104', '321 Elm St, City, State', 'M', 23, '2002-11-05'),
(105, 'MEM005', 'Emma Brown', 'emma.brown@email.com', '+1-555-0105', '654 Maple Dr, City, State', 'F', 20, '2005-05-18');

-- =====================================================
-- USEFUL VIEWS FOR REPORTING
-- =====================================================

-- View for available books with inventory
CREATE VIEW view_available_books AS
SELECT 
    b.book_id,
    b.book_id_isbn,
    b.title_of_book,
    a.name AS author_name,
    p.name AS publisher_name,
    c.name AS category_name,
    COALESCE(i.available_copies, 0) AS available_copies,
    COALESCE(i.total_copies, 1) AS total_copies,
    i.shelf_location,
    b.state_of_book,
    b.publication_date
FROM core_book b
JOIN core_author a ON b.author_id = a.id
JOIN core_publisher p ON b.publisher_id = p.id
JOIN core_category c ON b.category_id = c.id
LEFT JOIN core_inventory i ON b.book_id = i.book_id
WHERE b.is_available = 1;

-- View for overdue books
CREATE VIEW view_overdue_books AS
SELECT 
    br.borrow_id,
    m.name AS member_name,
    m.member_id,
    m.email AS member_email,
    b.title_of_book,
    a.name AS author_name,
    br.date_borrow,
    br.date_due,
    DATEDIFF(CURDATE(), br.date_due) AS days_overdue,
    (DATEDIFF(CURDATE(), br.date_due) * 1.00) AS estimated_fine
FROM student_borrow br
JOIN student_member m ON br.member_id = m.id
JOIN core_book b ON br.book_id = b.book_id
JOIN core_author a ON b.author_id = a.id
WHERE br.is_returned = 0 
AND br.date_due < CURDATE()
ORDER BY days_overdue DESC;

-- View for room booking summary
CREATE VIEW view_room_booking_summary AS
SELECT 
    r.room_name,
    r.room_number,
    r.room_type,
    r.capacity,
    r.hourly_rate,
    COUNT(rb.booking_id) AS total_bookings,
    COUNT(CASE WHEN rb.status = 'confirmed' THEN 1 END) AS confirmed_bookings,
    COUNT(CASE WHEN rb.status = 'pending' THEN 1 END) AS pending_bookings,
    COUNT(CASE WHEN rb.status = 'cancelled' THEN 1 END) AS cancelled_bookings,
    SUM(CASE WHEN rb.status = 'confirmed' THEN rb.total_cost ELSE 0 END) AS total_revenue
FROM room_management_room r
LEFT JOIN room_management_roombooking rb ON r.room_id = rb.room_id
WHERE r.is_active = 1
GROUP BY r.room_id, r.room_name, r.room_number, r.room_type, r.capacity, r.hourly_rate
ORDER BY total_revenue DESC;

-- View for member borrowing summary
CREATE VIEW view_member_summary AS
SELECT 
    m.member_id,
    m.name,
    m.email,
    COUNT(br.borrow_id) AS total_borrowings,
    COUNT(CASE WHEN br.is_returned = 0 THEN 1 END) AS current_borrowings,
    COUNT(CASE WHEN br.is_returned = 0 AND br.date_due < CURDATE() THEN 1 END) AS overdue_books,
    COUNT(r.reservation_id) AS active_reservations,
    SUM(CASE WHEN f.is_paid = 0 THEN f.amount ELSE 0 END) AS unpaid_fines,
    m.max_books,
    m.is_active
FROM student_member m
LEFT JOIN student_borrow br ON m.id = br.member_id
LEFT JOIN student_reservation r ON m.id = r.member_id AND r.status = 'active'
LEFT JOIN student_fine f ON m.id = f.member_id
GROUP BY m.id, m.member_id, m.name, m.email, m.max_books, m.is_active
ORDER BY m.name;

-- View for popular books
CREATE VIEW view_popular_books AS
SELECT 
    b.book_id,
    b.title_of_book,
    a.name AS author_name,
    c.name AS category_name,
    COUNT(br.borrow_id) AS borrow_count,
    COUNT(r.reservation_id) AS reservation_count,
    (COUNT(br.borrow_id) + COUNT(r.reservation_id)) AS total_demand,
    i.total_copies,
    ROUND((COUNT(br.borrow_id) + COUNT(r.reservation_id)) / i.total_copies, 2) AS demand_ratio
FROM core_book b
JOIN core_author a ON b.author_id = a.id
JOIN core_category c ON b.category_id = c.id
LEFT JOIN core_inventory i ON b.book_id = i.book_id
LEFT JOIN student_borrow br ON b.book_id = br.book_id
LEFT JOIN student_reservation r ON b.book_id = r.book_id
WHERE b.is_available = 1
GROUP BY b.book_id, b.title_of_book, a.name, c.name, i.total_copies
HAVING total_demand > 0
ORDER BY total_demand DESC, demand_ratio DESC;

-- =====================================================
-- INDEXES FOR PERFORMANCE (Additional)
-- =====================================================

-- Additional performance indexes for better query performance
CREATE INDEX idx_book_title_search ON core_book(title_of_book(50));
CREATE INDEX idx_member_email ON student_member(email);
CREATE INDEX idx_borrow_due_status ON student_borrow(date_due, is_returned);
CREATE INDEX idx_reservation_status_expires ON student_reservation(status, date_expires);
CREATE INDEX idx_fine_paid_amount ON student_fine(is_paid, amount);
CREATE INDEX idx_room_type_status ON room_management_room(room_type, status);
CREATE INDEX idx_booking_date_status ON room_management_roombooking(booking_date, status);

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

DELIMITER $$

-- Procedure to calculate overdue fine
CREATE PROCEDURE CalculateOverdueFine(
    IN p_borrow_id INT,
    IN p_daily_rate DECIMAL(5,2)
)
BEGIN
    DECLARE v_days_overdue INT DEFAULT 0;
    DECLARE v_fine_amount DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_member_id INT;
    DECLARE v_book_title VARCHAR(300);
    
    -- Get overdue days, member ID, and book title
    SELECT 
        DATEDIFF(CURDATE(), br.date_due),
        br.member_id,
        b.title_of_book
    INTO v_days_overdue, v_member_id, v_book_title
    FROM student_borrow br
    JOIN core_book b ON br.book_id = b.book_id
    WHERE br.borrow_id = p_borrow_id AND br.is_returned = 0;
    
    -- Calculate fine if overdue
    IF v_days_overdue > 0 THEN
        SET v_fine_amount = v_days_overdue * p_daily_rate;
        
        -- Insert fine record
        INSERT INTO student_fine (
            member_id, 
            borrow_record_id, 
            fine_type, 
            amount, 
            reason
        ) VALUES (
            v_member_id,
            p_borrow_id,
            'overdue',
            v_fine_amount,
            CONCAT('Book "', v_book_title, '" overdue by ', v_days_overdue, ' days at $', p_daily_rate, ' per day')
        );
        
        SELECT CONCAT('Fine of $', v_fine_amount, ' calculated for ', v_days_overdue, ' overdue days') AS result;
    ELSE
        SELECT 'Book is not overdue' AS result;
    END IF;
END$$

-- Procedure to get library statistics
CREATE PROCEDURE GetLibraryStatistics()
BEGIN
    SELECT 
        'Total Books' AS statistic,
        COUNT(*) AS value
    FROM core_book
    UNION ALL
    SELECT 
        'Available Books',
        COUNT(*)
    FROM core_book
    WHERE is_available = 1
    UNION ALL
    SELECT 
        'Total Members',
        COUNT(*)
    FROM student_member
    WHERE is_active = 1
    UNION ALL
    SELECT 
        'Active Borrowings',
        COUNT(*)
    FROM student_borrow
    WHERE is_returned = 0
    UNION ALL
    SELECT 
        'Overdue Books',
        COUNT(*)
    FROM student_borrow
    WHERE is_returned = 0 AND date_due < CURDATE()
    UNION ALL
    SELECT 
        'Total Rooms',
        COUNT(*)
    FROM room_management_room
    WHERE is_active = 1
    UNION ALL
    SELECT 
        'Available Rooms',
        COUNT(*)
    FROM room_management_room
    WHERE status = 'available' AND is_active = 1;
END$$

DELIMITER ;

-- =====================================================
-- SUMMARY INFORMATION
-- =====================================================

/*
MYSQL WORKBENCH READY SCRIPT
✅ Clean installation without DROP statements
✅ CREATE DATABASE and USE statements included
✅ 19 Custom Tables created in correct order
✅ All foreign key constraints properly defined
✅ Sample data for immediate testing (50+ records)
✅ 5 Useful reporting views
✅ Performance indexes for fast queries
✅ 2 Stored procedures for common operations
✅ Compatible with MySQL 8.0+ and MySQL Workbench

TABLES CREATED:
Core App (8 tables):
- core_userprofile, core_category, core_author, core_publisher
- core_donation, core_book, core_inventory, core_recycle, core_systemlog

Student App (5 tables):
- student_member, student_borrow, student_reservation
- student_fine, student_notification

Room Management App (4 tables):
- room_management_room, room_management_roomequipment
- room_management_roombooking, room_management_roommaintenance

Admin Custom App (1 table):
- admin_custom_staff

Plus 5 reporting views and 2 stored procedures for enhanced functionality.

READY TO RUN IN MYSQL WORKBENCH!
*/
