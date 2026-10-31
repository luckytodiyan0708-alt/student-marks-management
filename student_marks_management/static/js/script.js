/**
 * Student Marks Management System - Frontend JavaScript
 * Handles responsive sidebar navigation, form validation, and interactive UI behaviors.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebar = document.getElementById('sidebarMenu');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebarToggle) {
        // Create backdrop element
        const backdrop = document.createElement('div');
        backdrop.className = 'sidebar-backdrop d-none';
        document.body.appendChild(backdrop);

        const openSidebar = () => {
            sidebar.classList.add('show');
            backdrop.classList.remove('d-none');
        };

        const closeSidebar = () => {
            sidebar.classList.remove('show');
            backdrop.classList.add('d-none');
        };

        sidebarToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        backdrop.addEventListener('click', closeSidebar);

        // Close sidebar on ESC key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && sidebar.classList.contains('show')) {
                closeSidebar();
            }
        });
    }

    // 2. Bootstrap 5 Form Validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 3. Auto-dismiss Flash Alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {
                // Ignore if already dismissed
            }
        }, 6000);
    });
});

