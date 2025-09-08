/**
 * Form AutoSave - Saves form data to localStorage to prevent data loss on session expiry
 */

class FormAutoSave {
    constructor(formId, saveInterval = 30000) {
        this.formId = formId;
        this.form = document.getElementById(formId);
        this.saveInterval = saveInterval; // Default: save every 30 seconds
        this.storageKey = `autosave_${formId}_${window.location.pathname}`;
        this.timer = null;
        
        if (this.form) {
            this.init();
        } else {
            console.error(`Form with ID ${formId} not found`);
        }
    }
    
    init() {
        // Set up event listeners
        this.form.addEventListener('input', () => this.scheduleSave());
        this.form.addEventListener('submit', () => this.clearSavedData());
        
        // Check for saved data on page load
        this.checkForSavedData();
        
        // Start autosave timer
        this.startAutoSave();
        
        // Add restore button if saved data exists
        this.addRestoreButton();
    }
    
    scheduleSave() {
        // Clear any existing timer
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        // Schedule a new save
        this.timer = setTimeout(() => this.saveFormData(), 1000);
    }
    
    saveFormData() {
        const formData = this.getFormData();
        
        if (Object.keys(formData).length > 0) {
            // Save form data to localStorage
            localStorage.setItem(this.storageKey, JSON.stringify({
                timestamp: new Date().getTime(),
                data: formData
            }));
            
            console.log('Form data autosaved');
            
            // Show save indicator
            this.showSaveIndicator();
        }
    }
    
    getFormData() {
        const formData = {};
        const elements = this.form.elements;
        
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            const name = element.name;
            
            // Skip elements without a name, buttons, and submit inputs
            if (!name || element.type === 'button' || element.type === 'submit') {
                continue;
            }
            
            // Handle different input types
            if (element.type === 'checkbox' || element.type === 'radio') {
                if (element.checked) {
                    formData[name] = element.value;
                }
            } else if (element.type === 'select-multiple') {
                const selectedValues = [];
                for (let j = 0; j < element.options.length; j++) {
                    if (element.options[j].selected) {
                        selectedValues.push(element.options[j].value);
                    }
                }
                formData[name] = selectedValues;
            } else {
                formData[name] = element.value;
            }
        }
        
        // Handle special case for item rows in invoice/quotation forms
        const itemRows = document.querySelectorAll('.item-row');
        if (itemRows.length > 0) {
            formData['item_rows'] = [];
            itemRows.forEach((row, index) => {
                const nameInput = row.querySelector('[name^="item_name"]');
                const priceInput = row.querySelector('[name^="item_price"]');
                const quantityInput = row.querySelector('[name^="item_quantity"]');
                
                if (nameInput && priceInput && quantityInput) {
                    formData['item_rows'].push({
                        name: nameInput.value,
                        price: priceInput.value,
                        quantity: quantityInput.value
                    });
                }
            });
        }
        
        return formData;
    }
    
    checkForSavedData() {
        const savedData = localStorage.getItem(this.storageKey);
        
        if (savedData) {
            const parsedData = JSON.parse(savedData);
            const timestamp = new Date(parsedData.timestamp);
            const now = new Date();
            
            // Check if saved data is less than 24 hours old
            const hoursDiff = (now - timestamp) / (1000 * 60 * 60);
            
            if (hoursDiff < 24) {
                // Add restore notification
                this.showRestoreNotification(timestamp);
            } else {
                // Clear old data
                this.clearSavedData();
            }
        }
    }
    
    restoreFormData() {
        const savedData = localStorage.getItem(this.storageKey);
        
        if (savedData) {
            const parsedData = JSON.parse(savedData);
            const formData = parsedData.data;
            
            // Restore form fields
            for (const name in formData) {
                if (name === 'item_rows') {
                    // Handle special case for item rows
                    this.restoreItemRows(formData[name]);
                } else {
                    const elements = this.form.elements[name];
                    
                    if (elements) {
                        if (elements.length) {
                            // Handle radio buttons and multi-selects
                            for (let i = 0; i < elements.length; i++) {
                                const element = elements[i];
                                
                                if (element.type === 'radio') {
                                    element.checked = (element.value === formData[name]);
                                } else if (element.type === 'select-multiple') {
                                    for (let j = 0; j < element.options.length; j++) {
                                        element.options[j].selected = formData[name].includes(element.options[j].value);
                                    }
                                }
                            }
                        } else {
                            // Handle other input types
                            if (elements.type === 'checkbox') {
                                elements.checked = (elements.value === formData[name]);
                            } else {
                                elements.value = formData[name];
                            }
                        }
                    }
                }
            }
            
            // Recalculate totals if needed
            if (typeof calculateTotals === 'function') {
                calculateTotals();
            }
            
            console.log('Form data restored');
        }
    }
    
    restoreItemRows(itemRows) {
        // Clear existing rows except the first one
        const existingRows = document.querySelectorAll('.item-row');
        for (let i = existingRows.length - 1; i > 0; i--) {
            existingRows[i].remove();
        }
        
        // Clear the first row
        const firstRow = existingRows[0];
        if (firstRow) {
            const nameInput = firstRow.querySelector('[name^="item_name"]');
            const priceInput = firstRow.querySelector('[name^="item_price"]');
            const quantityInput = firstRow.querySelector('[name^="item_quantity"]');
            
            if (nameInput) nameInput.value = '';
            if (priceInput) priceInput.value = '';
            if (quantityInput) quantityInput.value = '';
        }
        
        // Add rows for each saved item
        itemRows.forEach((item, index) => {
            if (index === 0 && firstRow) {
                // Use the first row
                const nameInput = firstRow.querySelector('[name^="item_name"]');
                const priceInput = firstRow.querySelector('[name^="item_price"]');
                const quantityInput = firstRow.querySelector('[name^="item_quantity"]');
                
                if (nameInput) nameInput.value = item.name;
                if (priceInput) priceInput.value = item.price;
                if (quantityInput) quantityInput.value = item.quantity;
            } else {
                // Add a new row
                if (typeof addItemRow === 'function') {
                    addItemRow();
                    
                    // Get the newly added row
                    const rows = document.querySelectorAll('.item-row');
                    const newRow = rows[rows.length - 1];
                    
                    const nameInput = newRow.querySelector('[name^="item_name"]');
                    const priceInput = newRow.querySelector('[name^="item_price"]');
                    const quantityInput = newRow.querySelector('[name^="item_quantity"]');
                    
                    if (nameInput) nameInput.value = item.name;
                    if (priceInput) priceInput.value = item.price;
                    if (quantityInput) quantityInput.value = item.quantity;
                }
            }
        });
    }
    
    showRestoreNotification(timestamp) {
        const formattedTime = timestamp.toLocaleString();
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show';
        notification.innerHTML = `
            <strong>Unsaved data found!</strong> You have a draft saved on ${formattedTime}.
            <button type="button" id="restoreBtn" class="btn btn-sm btn-primary mx-2">Restore</button>
            <button type="button" id="discardBtn" class="btn btn-sm btn-secondary">Discard</button>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert at the top of the form
        this.form.insertBefore(notification, this.form.firstChild);
        
        // Add event listeners
        document.getElementById('restoreBtn').addEventListener('click', () => {
            this.restoreFormData();
            notification.remove();
        });
        
        document.getElementById('discardBtn').addEventListener('click', () => {
            this.clearSavedData();
            notification.remove();
        });
    }
    
    showSaveIndicator() {
        // Check if indicator already exists
        let indicator = document.getElementById('autosaveIndicator');
        
        if (!indicator) {
            // Create indicator
            indicator = document.createElement('div');
            indicator.id = 'autosaveIndicator';
            indicator.className = 'position-fixed bottom-0 end-0 m-3 p-2 bg-success text-white rounded shadow';
            indicator.style.opacity = '0';
            indicator.style.transition = 'opacity 0.3s';
            indicator.innerHTML = '<i class="fas fa-save me-2"></i> Draft saved';
            document.body.appendChild(indicator);
        }
        
        // Show indicator
        indicator.style.opacity = '1';
        
        // Hide after 2 seconds
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }
    
    startAutoSave() {
        // Save form data periodically
        setInterval(() => this.saveFormData(), this.saveInterval);
    }
    
    clearSavedData() {
        localStorage.removeItem(this.storageKey);
        console.log('Saved form data cleared');
    }
    
    addRestoreButton() {
        const savedData = localStorage.getItem(this.storageKey);
        
        if (savedData) {
            // Add a restore button to the form actions
            const formActions = this.form.querySelector('.form-actions');
            
            if (formActions) {
                const restoreButton = document.createElement('button');
                restoreButton.type = 'button';
                restoreButton.className = 'btn btn-outline-warning me-2';
                restoreButton.innerHTML = '<i class="fas fa-history me-2"></i> Restore Draft';
                restoreButton.addEventListener('click', () => this.restoreFormData());
                
                formActions.insertBefore(restoreButton, formActions.firstChild);
            }
        }
    }
}

// Initialize autosave on quotation and invoice forms
document.addEventListener('DOMContentLoaded', function() {
    const quotationForm = document.getElementById('quotationForm');
    const invoiceForm = document.getElementById('invoiceForm');
    
    if (quotationForm) {
        new FormAutoSave('quotationForm');
    }
    
    if (invoiceForm) {
        new FormAutoSave('invoiceForm');
    }
});