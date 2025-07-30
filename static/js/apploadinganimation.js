function showAppLoadingAnimation() {
    const loadingDiv = document.querySelector('.main-loading-animation');
    loadingDiv.innerHTML = `
        <div class="main-loading-animation-content">
            <div class="rotating-circle"></div>
            <img src="/static/images/foodhublogo.png" alt="">
        </div>
        <h3 style="text-align: center; margin-top: 0px;">MVGRCE<br>
            <p style="font-size: 8px; margin: 0px;">Captive Hospitality Services</p>
        </h3>
    `;
    loadingDiv.style.display = 'flex';
     document.body.style.overflow = 'hidden'; 
}

function hideAppLoadingAnimation() {
    document.querySelector('.main-loading-animation').style.display = 'none';
    document.body.style.overflow = ''; 
}