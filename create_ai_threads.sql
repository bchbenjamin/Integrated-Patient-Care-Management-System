CREATE TABLE IF NOT EXISTS ai_threads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

ALTER TABLE patients ADD COLUMN chat_retention_hours INT DEFAULT 1;
