document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('show');
            document.body.classList.toggle('menu-open');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (mobileMenu && mobileMenu.classList.contains('show')) {
            if (!mobileMenu.contains(event.target) && event.target !== menuToggle) {
                mobileMenu.classList.remove('show');
                document.body.classList.remove('menu-open');
            }
        }
    });
    
    // Handle recurring activity toggle
    const recurringCheckbox = document.getElementById('is-recurring');
    const recurringOptions = document.querySelector('.recurring-options');
    
    if (recurringCheckbox && recurringOptions) {
        recurringCheckbox.addEventListener('change', function() {
            if (this.checked) {
                recurringOptions.style.display = 'block';
            } else {
                recurringOptions.style.display = 'none';
            }
        });
    }
    
    // Add more inventory items to activity form
    const addInventoryButton = document.getElementById('add-inventory-item');
    const inventoryItemsContainer = document.getElementById('inventory-items');
    
    if (addInventoryButton && inventoryItemsContainer) {
        addInventoryButton.addEventListener('click', function() {
            const itemTemplate = inventoryItemsContainer.querySelector('.inventory-item').cloneNode(true);
            
            // Clear values
            const selectInput = itemTemplate.querySelector('select');
            const quantityInput = itemTemplate.querySelector('input');
            
            if (selectInput) selectInput.value = '';
            if (quantityInput) quantityInput.value = '';
            
            // Add remove button
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'btn btn-sm btn-danger remove-item';
            removeButton.innerHTML = 'X';
            removeButton.style.marginLeft = '10px';
            
            removeButton.addEventListener('click', function() {
                this.parentNode.parentNode.remove();
            });
            
            itemTemplate.querySelector('.col-5').appendChild(removeButton);
            
            // Add to container
            inventoryItemsContainer.appendChild(itemTemplate);
        });
    }
    
    // Weather data handling
    const weatherForm = document.getElementById('weather-form');
    const locationInput = document.getElementById('weather-location');
    
    if (weatherForm && locationInput) {
        weatherForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const location = locationInput.value.trim();
            if (!location) {
                alert('Please enter a location');
                return;
            }
            
            try {
                // In a real app, you would fetch this from a weather API
                // For now, we'll simulate weather data for demo purposes
                const weatherData = {
                    location: location,
                    date: new Date().toISOString().split('T')[0],
                    temperature: Math.round(10 + Math.random() * 25), // 10-35°C
                    humidity: Math.round(40 + Math.random() * 50), // 40-90%
                    precipitation: parseFloat((Math.random() * 10).toFixed(1)), // 0-10mm
                    wind_speed: parseFloat((2 + Math.random() * 18).toFixed(1)), // 2-20km/h
                    conditions: ['Sunny', 'Cloudy', 'Rainy', 'Overcast', 'Thunderstorm'][Math.floor(Math.random() * 5)]
                };
                
                // Update UI with weather data
                const weatherDisplay = document.getElementById('weather-display');
                if (weatherDisplay) {
                    weatherDisplay.innerHTML = `
                        <div class="weather-card">
                            <div class="weather-header">
                                <h3>${weatherData.location}</h3>
                                <p>Today: ${weatherData.date}</p>
                            </div>
                            <div class="weather-body">
                                <div class="weather-temp">${weatherData.temperature}°C</div>
                                <div class="weather-condition">${weatherData.conditions}</div>
                                <ul class="weather-details">
                                    <li><i class="fas fa-tint"></i> Humidity: ${weatherData.humidity}%</li>
                                    <li><i class="fas fa-cloud-rain"></i> Precipitation: ${weatherData.precipitation}mm</li>
                                    <li><i class="fas fa-wind"></i> Wind: ${weatherData.wind_speed}km/h</li>
                                </ul>
                            </div>
                        </div>
                    `;
                }
                
                // Save weather data to server
                const response = await fetch('/weather', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(weatherData)
                });
                
                const result = await response.json();
                console.log('Weather data saved:', result);
                
            } catch (error) {
                console.error('Error updating weather:', error);
            }
        });
    }
    
    // If we're on the inventory page, add some chart visualizations (placeholder)
    if (document.querySelector('.inventory-section')) {
        console.log('Inventory page loaded - would initialize charts here');
    }
    
    // If we're on the activity page, add some chart visualizations (placeholder)
    if (document.querySelector('.activity-section')) {
        console.log('Activity page loaded - would initialize charts here');
    }
});

// Function to format dates for display
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return 'Today';
    } else if (diffDays === 1) {
        return date > now ? 'Tomorrow' : 'Yesterday';
    } else if (diffDays < 7) {
        return date > now ? `In ${diffDays} days` : `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}