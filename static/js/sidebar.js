document.addEventListener('DOMContentLoaded', function() {
    // Get sidebar elements
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileSidebarToggle');
    const body = document.body;
    
    // Check if elements exist before proceeding
    if (!sidebar || !mainContent) {
        console.warn('Sidebar or mainContent elements not found');
        return;
    }
    
    // Function to check if we're on mobile
    const isMobile = () => window.innerWidth <= 768;
    
    // Check for saved sidebar state (only apply on desktop)
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    
    // Initialize sidebar state based on saved preference (only on desktop)
    if (!isMobile() && sidebarState === 'true') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
    }
    
    // Toggle sidebar on desktop button click
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            // Save sidebar state (only on desktop)
            if (!isMobile()) {
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
        });
    }
    
    // Mobile sidebar toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('expanded');
            body.classList.toggle('sidebar-active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (isMobile() && 
                sidebar && !sidebar.contains(event.target) && 
                mobileToggle && !mobileToggle.contains(event.target) &&
                sidebar.classList.contains('expanded')) {
                sidebar.classList.remove('expanded');
                body.classList.remove('sidebar-active');
            }
        });
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (isMobile()) {
            // On mobile, remove collapsed class and add appropriate classes
            sidebar.classList.remove('collapsed');
            if (!sidebar.classList.contains('expanded')) {
                body.classList.remove('sidebar-active');
            }
        } else {
            // On desktop, remove expanded and apply saved state
            sidebar.classList.remove('expanded');
            body.classList.remove('sidebar-active');
            
            if (sidebarState === 'true') {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('expanded');
            } else {
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('expanded');
            }
        }
    });
    
    // Mark current page as active in sidebar
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    
    if (sidebarLinks && sidebarLinks.length > 0) {
        sidebarLinks.forEach(link => {
            if (link) {
                const linkPath = link.getAttribute('href');
                if (currentPath === linkPath || (currentPath.startsWith(linkPath) && linkPath !== '/')) {
                    link.classList.add('active');
                }
            }
        });
    }
});