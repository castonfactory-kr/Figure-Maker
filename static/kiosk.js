document.addEventListener('DOMContentLoaded', () => {
    const styleCards = document.querySelectorAll('.kiosk-style-card');
    const paymentBtn = document.getElementById('paymentBtn');
    
    let selectedStyle = null;

    styleCards.forEach(card => {
        card.addEventListener('click', () => {
            styleCards.forEach(c => {
                c.classList.remove('selected');
                c.querySelector('.style-check').classList.add('hidden');
            });

            card.classList.add('selected');
            card.querySelector('.style-check').classList.remove('hidden');
            
            selectedStyle = card.dataset.style;
            paymentBtn.disabled = false;
        });
    });

    paymentBtn.addEventListener('click', () => {
        if (selectedStyle) {
            window.location.href = `/static/kiosk-payment.html?style=${selectedStyle}`;
        }
    });
});
