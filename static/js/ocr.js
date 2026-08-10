/**
 * Ease Health — OCR Module
 * Handles file uploads for prescription OCR.
 * Files are sent to /ai/ocr endpoint on the backend.
 * 
 * Usage:
 *   <script src="/static/js/ocr.js"></script>
 *   EaseOCR.processFile(file, context);
 */
const EaseOCR = (function() {
    'use strict';

    // Track pending file
    window.__pendingFile = null;

    function handleFileSelect(input) {
        const file = input.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload an image (JPEG, PNG) or PDF file.');
            input.value = '';
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB.');
            input.value = '';
            return;
        }

        window.__pendingFile = file;
        showPreview(file);
    }

    function showPreview(file) {
        const previewArea = document.getElementById('file-preview-area');
        const previewName = document.getElementById('file-preview-name');
        if (!previewArea || !previewName) return;

        previewName.textContent = file.name + ' (' + formatFileSize(file.size) + ')';
        previewArea.style.display = 'block';
    }

    function clearFileUpload() {
        window.__pendingFile = null;
        const previewArea = document.getElementById('file-preview-area');
        if (previewArea) previewArea.style.display = 'none';
        const input = document.getElementById('ocr-file-input');
        if (input) input.value = '';
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    async function processFile(file, context) {
        const formData = new FormData();
        formData.append('file', file);
        if (context) formData.append('context', context);

        try {
            const response = await fetch('/ai/ocr', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                return { error: errorData.detail || 'Failed to process file.' };
            }
            
            return await response.json();
        } catch (error) {
            console.error('OCR processing error:', error);
            return { error: 'Network error. Please try again.' };
        }
    }

    // Make functions globally available (used by inline handlers in chat.html)
    window.handleFileSelect = handleFileSelect;
    window.clearFileUpload = clearFileUpload;

    return {
        handleFileSelect,
        clearFileUpload,
        processFile,
        formatFileSize
    };
})();
