document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    
    const mobileMenuButton = document.createElement('button');
    mobileMenuButton.className = 'mobile-menu-button';
    mobileMenuButton.innerHTML = '<i class="fas fa-bars"></i>';
    
    const navContainer = document.querySelector('.nav-container');
    const navMenu = document.querySelector('.nav-menu');
    
    if (window.innerWidth <= 768) {
        navContainer.insertBefore(mobileMenuButton, navMenu);
        navMenu.style.display = 'none';
        
        mobileMenuButton.addEventListener('click', function() {
            navMenu.style.display = navMenu.style.display === 'none' ? 'flex' : 'none';
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            navMenu.style.display = 'flex';
            if (mobileMenuButton.parentNode) {
                mobileMenuButton.parentNode.removeChild(mobileMenuButton);
            }
        } else {
            if (!mobileMenuButton.parentNode) {
                navContainer.insertBefore(mobileMenuButton, navMenu);
            }
            navMenu.style.display = 'none';
        }
    });

    // Add animation to cards on scroll
    const cards = document.querySelectorAll('.card');
    
    const observerOptions = {
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
}); 