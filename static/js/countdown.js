function updateCountdown() {
    const countdownElement = document.getElementById('compteur-temps-restant');
    if (!countdownElement) {
        return; // Exit if the element is not found on the page
    }

    let tempsRestant = parseInt(countdownElement.dataset.tempsRestant);

    if (isNaN(tempsRestant) || tempsRestant <= 0) {
        countdownElement.innerHTML = '<i class="fas fa-lock me-1"></i>Application bloquée';
        countdownElement.classList.remove('bg-warning', 'text-dark');
        countdownElement.classList.add('bg-danger', 'text-white');
        return; // Stop the countdown
    }

    tempsRestant--;
    countdownElement.dataset.tempsRestant = tempsRestant;

    const hours = Math.floor(tempsRestant / 3600);
    const minutes = Math.floor((tempsRestant % 3600) / 60);
    const seconds = tempsRestant % 60;

    const formattedTime = [
        hours.toString().padStart(2, '0'),
        minutes.toString().padStart(2, '0'),
        seconds.toString().padStart(2, '0')
    ].join(':');

    countdownElement.innerHTML = `<i class="fas fa-hourglass-half me-1"></i>${formattedTime}`;

    if (tempsRestant <= 3600 * 24 && tempsRestant > 0) { // Less than 24 hours (86400 seconds)
        countdownElement.classList.remove('bg-success');
        countdownElement.classList.add('bg-warning');
    } else if (tempsRestant <= 0) {
        countdownElement.classList.remove('bg-warning', 'text-dark');
        countdownElement.classList.add('bg-danger', 'text-white');
        countdownElement.innerHTML = '<i class="fas fa-lock me-1"></i>Application bloquée';
    }
}

// Initial call to display immediately
// updateCountdown();

// Update every second
// setInterval(updateCountdown, 1000); 