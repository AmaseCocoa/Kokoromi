document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = themeToggleBtn.querySelector('i');
    
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.body.classList.toggle('light-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            themeIcon.classList.remove('bi-moon');
            themeIcon.classList.add('bi-sun');
            themeToggleBtn.textContent = ' ライトモード';
        } else {
            themeIcon.classList.remove('bi-sun');
            themeIcon.classList.add('bi-moon');
            themeToggleBtn.textContent = ' ダークモード';
        }
    });
});
