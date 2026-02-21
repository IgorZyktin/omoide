let touchStartX = 0;
let touchEndX = 0;
const swipeThreshold = 50;

function openNav() {
    // Open side menu
    document.getElementById("navbar").classList.add("sidenav-open");
}

function closeNav() {
    // Close side menu
    document.getElementById("navbar").classList.remove("sidenav-open");
}

function handleGesture() {
    // React on user gestures
    const swipeDistance = touchEndX - touchStartX;
    let open = document.getElementById("navbar").classList.contains('sidenav-open')

    // Check if the menu is closed and the swipe is from the left edge
    if (!open && swipeDistance > swipeThreshold) {
        openNav()
    }

    // Check if the menu is open and the swipe is a leftward motion
    if (open && swipeDistance < -swipeThreshold) {
        closeNav()
    }
}
