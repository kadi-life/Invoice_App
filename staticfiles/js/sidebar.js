document.addEventListener('DOMContentLoaded', function() {
    // Get sidebar elements
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileSidebarToggle');
    
    // Check if elements exist before proceeding
    if (!sidebar || !mainContent) {
        console.warn('Sidebar or mainContent elements not found');
        return;
    }
    
    // Check for saved sidebar state
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    
    // Initialize sidebar state based on saved preference
    if (sidebarState === 'true') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
    }
    
    // Toggle sidebar on button click
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            // Save sidebar state
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }
    
    // Mobile sidebar toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('expanded');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            const windowWidth = window.innerWidth;
            
            if (windowWidth <= 768 && 
                sidebar && !sidebar.contains(event.target) && 
                mobileToggle && !mobileToggle.contains(event.target) &&
                sidebar.classList.contains('expanded')) {
                sidebar.classList.remove('expanded');
            }
        });
    }
    
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