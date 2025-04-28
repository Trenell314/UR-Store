document.addEventListener('DOMContentLoaded', function() {
    const productContainer = document.getElementById('products-container');
    const filterBtn = document.getElementById('filter-btn');
    const categoryFilter = document.getElementById('category-filter');
    
    console.log('Product container:', productContainer);
    console.log('Filter button:', filterBtn);
    console.log('Category filter:', categoryFilter);

    if (!productContainer || !filterBtn || !categoryFilter) {
        console.error('Critical elements missing!');
        return;
    }

    function applyFilter() {
        const selectedCategory = categoryFilter.value.toLowerCase();
        const productCards = productContainer.getElementsByClassName('product-card');
        
        Array.from(productCards).forEach(card => {
            const cardCategory = card.dataset.category.toLowerCase();
            const shouldShow = selectedCategory === 'all' || cardCategory === selectedCategory;
            card.style.display = shouldShow ? 'block' : 'none';
        });
    }

    applyFilter();

    function setupEventListeners() {
        try {
            filterBtn.addEventListener('click', function(e) {
                e.preventDefault();
                applyFilter();
            });
            
            categoryFilter.addEventListener('change', applyFilter);
        } catch (error) {
            console.error('Error setting up event listeners:', error);
        }
    }
    setupEventListeners();

    productContainer.addEventListener('submit', async function(e) {
        if (e.target.classList.contains('delete-form')) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to delete this product?')) return;

            const form = e.target;
            const productCard = form.closest('.product-card');
            
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({
                        csrf_token: form.querySelector('[name="csrf_token"]').value
                    })
                });

                if (response.ok) {
                    productCard.style.transition = 'opacity 0.3s, height 0.3s';
                    productCard.style.opacity = '0';
                    productCard.style.height = '0';
                    productCard.style.margin = '0';
                    productCard.style.padding = '0';
                    productCard.style.border = 'none';
                    
                    setTimeout(() => {
                        productCard.remove();
                    }, 300);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Delete failed');
                }
            } catch (error) {
                console.error('Delete error:', error);
                alert(`Delete failed: ${error.message}`);
            }
        }
    });

    console.log('Filter initialized successfully');
});