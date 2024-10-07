function toggleSidebar() {
    var sidebar = document.getElementById("mySidebar");
    var mainContent = document.getElementById("mainContent"); 
    sidebar.classList.toggle("show");
}
document.addEventListener('DOMContentLoaded', function() { 
    const themeToggle = document.getElementById('themeControlToggle');
    const body = document.body;

    themeToggle.addEventListener('change', () => {
        body.classList.toggle('dark-mode');
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });

    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.checked = true; 
    }
});