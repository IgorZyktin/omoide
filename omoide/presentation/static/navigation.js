let touchStartX = 0;
let touchStartY = 0;
let touchEndX = 0;
let touchEndY = 0;
const swipeThresholdX = 100;
const swipeThresholdY = 200;

function openNav() {
    // Open side menu
    document.getElementById("navbar").classList.add("sidenav-open");
    document.getElementById("opaque").style.display = "block";
    document.getElementById("content").style.filter = "grayscale(100%)";
}

function closeNav() {
    // Close side menu
    document.getElementById("navbar").classList.remove("sidenav-open");
    document.getElementById("opaque").style.display = "none";
    document.getElementById("content").style.filter = "none";
}

function handleGesture() {
    // React on user gestures
    const swipeDistanceX = touchEndX - touchStartX;
    const swipeDistanceY = Math.abs(touchEndY - touchStartY);
    let open = document.getElementById("navbar").classList.contains('sidenav-open');

    // Check if the menu is closed and the swipe is from the left edge
    if (!open && swipeDistanceX > swipeThresholdX && swipeDistanceY < swipeThresholdY) {
        openNav()
    }

    // Check if the menu is open and the swipe is a leftward motion
    if (open && swipeDistanceX < -swipeThresholdX && swipeDistanceY < swipeThresholdY) {
        closeNav()
    }
}
