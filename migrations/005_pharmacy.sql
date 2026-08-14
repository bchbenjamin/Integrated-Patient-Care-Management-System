CREATE TABLE IF NOT EXISTS pharmacy_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    category ENUM('otc', 'prescription') NOT NULL DEFAULT 'otc',
    description TEXT,
    dosage_form VARCHAR(100),
    strength VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    quantity INT NOT NULL DEFAULT 0,
    image_url VARCHAR(500),
    requires_prescription BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed with common OTC medicines
INSERT INTO pharmacy_stock (medicine_name, generic_name, category, description, dosage_form, strength, price, quantity, requires_prescription) VALUES
('Paracetamol', 'Acetaminophen', 'otc', 'Pain reliever and fever reducer', 'Tablet', '500mg', 2.99, 500, FALSE),
('Ibuprofen', 'Ibuprofen', 'otc', 'Anti-inflammatory pain reliever', 'Tablet', '200mg', 4.49, 300, FALSE),
('Cetirizine', 'Cetirizine HCl', 'otc', 'Antihistamine for allergy relief', 'Tablet', '10mg', 5.99, 200, FALSE),
('Omeprazole', 'Omeprazole', 'otc', 'Acid reflux and heartburn relief', 'Capsule', '20mg', 8.99, 150, FALSE),
('Loperamide', 'Loperamide HCl', 'otc', 'Anti-diarrheal medication', 'Capsule', '2mg', 3.99, 250, FALSE),
('Diphenhydramine', 'Diphenhydramine HCl', 'otc', 'Antihistamine and sleep aid', 'Capsule', '25mg', 4.29, 200, FALSE),
('Aspirin', 'Acetylsalicylic Acid', 'otc', 'Pain reliever and blood thinner', 'Tablet', '325mg', 3.49, 400, FALSE),
('Guaifenesin', 'Guaifenesin', 'otc', 'Expectorant for chest congestion', 'Tablet', '400mg', 5.49, 180, FALSE),
('Dextromethorphan', 'Dextromethorphan HBr', 'otc', 'Cough suppressant', 'Syrup', '15mg/5ml', 6.99, 120, FALSE),
('Bismuth Subsalicylate', 'Bismuth Subsalicylate', 'otc', 'Stomach relief for nausea and indigestion', 'Liquid', '262mg/15ml', 5.99, 100, FALSE),
('Hydrocortisone Cream', 'Hydrocortisone', 'otc', 'Anti-itch and anti-inflammatory cream', 'Cream', '1%', 7.49, 150, FALSE),
('Saline Nasal Spray', 'Sodium Chloride', 'otc', 'Nasal moisturizer and decongestant', 'Spray', '0.65%', 4.99, 200, FALSE),
('Antacid Tablets', 'Calcium Carbonate', 'otc', 'Fast-acting heartburn and acid relief', 'Chewable Tablet', '500mg', 3.29, 350, FALSE),
('Vitamin D3', 'Cholecalciferol', 'otc', 'Bone health and immune support', 'Softgel', '1000 IU', 6.49, 250, FALSE),
('Zinc Lozenges', 'Zinc Gluconate', 'otc', 'Immune support and cold symptom relief', 'Lozenge', '13.3mg', 5.79, 200, FALSE),
('Melatonin', 'Melatonin', 'otc', 'Natural sleep aid supplement', 'Tablet', '3mg', 4.99, 300, FALSE),
('Electrolyte Powder', 'Oral Rehydration Salts', 'otc', 'Rehydration for illness and exercise', 'Powder', '20g sachet', 1.99, 500, FALSE),
('Bandage Roll', 'Gauze Bandage', 'otc', 'Sterile wound dressing roll', 'Roll', '4 inch x 5 yards', 2.49, 400, FALSE),
('Antiseptic Solution', 'Povidone-Iodine', 'otc', 'Wound cleaning and disinfection', 'Solution', '10%', 3.99, 200, FALSE),
('Eye Drops', 'Artificial Tears', 'otc', 'Lubricating eye drops for dry eyes', 'Drops', '15ml', 7.99, 150, FALSE);
